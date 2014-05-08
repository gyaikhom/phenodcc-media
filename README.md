# Media file download and processing

This describes the implementation of the software module which automates downloading and processing of media files. It is expected to be run periodically as part of a data collection service at the [IMPC](http://mousephenotype.org) data coordination centre.

The data coordination centre uses an automated system, referred to as the **[crawler](https://github.com/mpi2/phenodcc-crawler)**, for data collection and collation. It crawls all of the participating research institutes periodically, and downloads all of the data that have been added since the last crawling session. In addition to alpha-numeric data, the centres also export media data (e.g., X-ray images, 3D embryo models etc.), which the crawler should handle. The media file downloader implements this facility.

## Usage

To run the script, you will require sufficient storage space allocated for the original media files and processed files (e.g., thumbnails and image tiles). This storage should be read and write accessible to the scripts.

Let us assume that the allocate directory where we wish to download and store our files is `/media/`. We must do the following to run the scripts.

1. Create an archival directory for storing the original media files:

        $ cd /media
        $ mkdir src
    
2. Create directory for storing processed files:

        $ mkdir tiles

3. Create the `phenodcc_media` database by running the `phenodcc_media.sql` script. Check the top of the file for adding users and credentials etc.

4. Modify the `phenodcc_media.config` properties file to set the database access credentials and the target directories created in steps 1 and 2.

5. Alter the Python script `downloader.py` to match your setup for retrieving the URIs which we wish to download and process.

6. Run `downloader.py`.


After a successful run, the contents of the directories will be as follows:

* `src`
    This contains all of the original media files.

* `tiles`
    This contains all of the image tiles and thumbnails generated from the original image files.

The script can be **run incrementally**. During each run, only files that have not been downloaded in the previous run will be downloaded. In addition to these new URIs, the script will also attempt to download media that could not be downloaded in previous runs. Furthermore, existing files and directories are left untouched.

## Implementation requirements

Research centres exporting media data hosts their media files at their respective servers (e.g., FTP server). The URI (uniform resource identifier) of these media files are supplied to the crawler as string values of experimental results. This is what the downloader module uses as the source for retrieving the media files.

The following are the key design challenges:

1. The module should integrate seamlessly with the **crawler**.
2. The original media should be processed to make dissemination efficient.
3. The processing should also reduce storage requirements.
4. All of the media files retrieved from the various host servers should be archived for future access.

## Source code structure

The [Python](https://www.python.org/) script `downloader.py` carries out the downloading and processing. This script should be executed periodically by the **crawler**.

Not all media files need processing (e.g., PDF files). However, for most of the media files that are images, the download module should optimise the image files for efficient delivery. This processing is done by the `generate_tiles.sh` [Bash](https://www.gnu.org/software/bash/) script.

Since the URIs are provided to the module as string values of experimental results, the module requires access to the database where these values are stored. The access credential to this database is specified in the `phenodcc_media.config` properties file.

To archive the media files downloaded and to generate processed files for efficient dissemination, we need storage. As discussed in the _Usage_ section, we need two directories for storing files. These are also specified in `phenodcc_media.config`.

Finally, to keep track of the state of media files that the module has already processed, and those that need processing, the module maintains a database. The schema for this database is specified in the [MySQL](http://www.mysql.com/) script `phenodcc_media.sql`.

## Storage architecture

We expect the system to store a large number of media files. This presents the following challenges:

### Structured archive

The archive should be structured so that we can infer the original experiment context from the directory structure. At the IMPC, a unique set of media files are generated for each of the specimens that are subjects of an experiment context. This context is uniquely identified by the _centre_ (`cid`), _experiment pipeline_ (`lid`), _genotype_ (`gid`), _strain_ (`sid`), _experimental procedure_ (`pid`) and the _measured parameter_ (`qid`). Hence, we choose the following directory structure for storing the original media files inside the archive directory `src`:

    src/{cid}/{lid}/{gid}/{sid}/{pid}/{qid}

Now, since we create a record in `phenodcc_media.media_file` for each media file that the module should track, it uses the _primary key_ of this record to name the media file that is downloaded and saved. We could also use the _measurement identifier_ (`mid`) associated with the media file URI.

We could have saved the media files using the file name in the URI, however, since there is no standardisation across centres on how the files should be named, it hinders automation. Again, since the original file names are of little concern to us, given that we can refer back to the context from the `<cid, lid, gid, sid, pid, qid>` tuple, using the primary key makes maintenance much easier.

## Optimising storage

We do not wish to store the same data multiple times. While we have to keep the original files for archival purposes, the processed files should not be replicated. This means:

1. Only store processed files that are unique.
2. Prevent the module from processing files that have already been processed, if the data is not unique.

To achieve this, all of the media files that are to be processed are first filtered out by their _content_ checksum. Once a file has been downloaded and saved in the archive directory `src`, we calculate its [SHA1](http://en.wikipedia.org/wiki/SHA-1) checksum.

* If the checksum is new, we create a new checksum directory inside `tiles` directory and generate all of the images tiles and thumbnails inside this directory. The checksum is then recorded in the `phenodcc_media.media_file` table.
 
* If the checksum already exists in `phenodcc_media.media_file` table, we do not process the media file again since we can reuse the existing processed files (e.g., tiles, thumbnails etc.). Hence, we simply update the corresponding record in `phenodcc_media.media_file` to point to this directory.

### Directory structure

Now, depending on the file system, the number of items allowed inside a directory varies. Furthermore, listing a flat directory structure of checksum directory names will be extremely slow, considering that there will be a large amount of image data. To alleviate this issue, we break the checksum into a directory hierarchy. For instance, instead of saving the process files inside a directory named, say `004303cc748c45f718b71ffeb71505a87e0b4bf0`, we break it down into a path `0043/03cc/748c/45f7/18b7/1ffe/b715/05a8/7e0b/4bf0`. Since SHA1 checksums are 40 characters long, we can have a hierarchy that is 10 paths depth. This tree spreads out the flat directory, which is much more efficient and works around the file system limitations.

### Generating the tiles

All of the image files should be delivered efficiently. This means that the files should not be too big to download, and that the server should spend as little as possible on delivering the files. Based on this, we take advantage of the following:

1. Choose appropriate image compression for size optimisation.
2. Choose an image container that is readily supported by most browsers.
3. Only download parts of the image that are visible to the client.

Based on these requirements, we have the following:

1. Convert all image media data to JPEG. This means converting DICOM, TIFF, BMP etc. to JPEG.

2. Break the original image to smaller image tiles. This allows downloading only parts of the image that are visible to the client.

We use [ImageMagick](http://www.imagemagick.org/) to do the conversion and tiling. For each image file downloaded, the `generate_tiles.sh` script goes to the checksum directory and converts the original media file to a JPEG image named `original.jpg`. Then, for each of the requested scales, `original.jpg` file is broken down into tiles.

In the `phenodcc_media.config`, we can specify the size of the tile (in pixels) and also the set of scaling that we require. For instance,

    [tiling]
    tile_sizes = 128,256
    image_scales = 10,25,50,75,100

Further to the tiles, the script also generates a thumbnail file, which can be used inside image navigators.
