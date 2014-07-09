# Media downloader and image processor

The `phenodcc_media.py` script allows a user to prepare, download and process media files.
If the media files are images, the required tiles are generated for efficient dissemination.
For the design documentation, see `docs/` directory.

## Usage

To run the script, you must use one of the command-line switches, as shown below:

    $ ./phenodcc_media.py -h

    PhenoDCC media downloader and tile generator
    (http://www.mousephenotype.org)
    Version 1.0.0 
    
    USAGE: phenodcc_media.py [-p | --prepare | -d | --download | -t | --tile | -v | --verbose | -h | --help]
    
        -p, --prepare    Prepare media files by marking them for download.
        -d, --download   Download media files that was marked for download.
        -t, --tile       Generate tiles for all of the image media files
                         that was downloaded successfully.
        -v, --verbose    Verbose output of execution status.
        -h, --help       Displays this help information.
    
    The configuration file for running this script is set in 'phenodcc_media.config'.
    The following settings are allowed:
    
        tracker - Database for getting active contexts and media file URLs.
          media - Database where we track the download and processing of media files.
           tile - Set tile size.
         scales - Set zooming scales.

## Step-by-step instructions

The following provides a step-by-step guide to running the media downloader.

1. Set the `phenodcc_media.config` file.
    * Which database should the downloader use to get the media file URLs?
    * Which database should the downloader use for keeping track of the download and processing?
    * Where should the downloader store the original media and associated generated tiles.
    * What should be the maximum dimensions (in pixels) of the generated tiles?
    * What zoom levels should the tiles accommodate?
 
2. Make sure that the user has access to the above databases and file system.
3. You can run all three phases (prepare, download and tiling) simultaneously.
   If you wish to run them sequentially, here are the steps:
    
     $ cd /home/user/phenodcc-media/src
     $ ./phenodcc_media.py -p -v
     $ ./phenodcc_media.py -d -v
     $ ./phenodcc_media.py -t -v


## Single Instance

To allow the script to be invoked periodically as part of an automated system,
the script uses file locking to allow only one running instance of a phase.
Hence, a file named `prepare.lock`, `download.lock` or `tiling.lock` is created in the
directory from which the script is invoked. Note that this only works if the script
is always run from the same directory. Two different phases can run simultaneously.


## Files and their meaning

* `download.lock` - Lock file that prevents multiple instances of the **download** phase. If a script was executed
    previously in the _download mode_, and if it is still running, no new **download** phase can be instantiated.

* `fix_tile_metadata.py` - _Ad hoc_ script that was used to fix image file meta-data when the tiling was run
    independently of the database. This fixes the checksum and image dimensions for each of the image media records
    in the database. Note that tiling of an entire _source_ directory tree can be achieve independently of the
    database by running the `generate_tiles_using_source_directory.sh` script.

* `generate_tiles_for_image.sh` - This script generates the required tiles for a given image media. It is used by
    the **tiling** phase to generate tiles for a given tiling configuration.

* `generate_tiles_using_source_directory.sh` - This script generate all of the required tiles for a collection of
    image media. This is run independently of the `phenodcc_media.py` script. Use this script only when tiles
    must be generated without modifying the `phenodcc_media` database. Remember to run `fix_tile_metadata.py`
    if you wish to sync the tiles with the database.

* `phenodcc_media.config` - This is the configuration file that is used by `phenodcc_media.py` to run each of
    the phases. You set here the `phenodcc_tracker` database, `phenodcc_media` database, tile size,
    zoom levels required for tiling etc.

* `phenodcc_media.py` - This is the main script. It can be run in one of the three phases: **prepare**, **download**
   or **tiling**. The behaviour of the script depends not only on the command line switches, but also on the
   values set in `phenodcc_media.config`.

* `phenodcc_media.sql` - This is the script for creating the `phenodcc_media` database. The linking between media files,
    tiles and the image display web application relies completely on this database.

* `prepare.lock` - Lock file that prevents multiple instances of the **prepare** phase. If a script was executed
    previously in the _prepare mode_, and if it is still running, no new **prepare** phase can be instantiated.

* `tiling.lock` - Lock file that prevents multiple instances of the **tiling** phase. If a script was executed
    previously in the _tiling mode_, and if it is still running, no new **tiling** phase can be instantiated.

