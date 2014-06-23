# PhenoDCC Image Viewer

The _PhenoDCC image viewer_ allows biologists to observe phenotypic
variation between mutants and wildtypes as a result of genetic
mutations. It supports side-by-side comparison of images that belong
to mutants and wildtypes (for instance, the variation in skeletal
structure as made visible through X-ray images).

![Screenshot of Image Viewer](screenshot.jpg)


# Implementation guidelines

The viewer has three main components:

* **Processing** The image data submitted to the PhenoDCC comes in
    various formats. These are BMP, DICOM, JPEG, PNG and TIFF. Since
    the image viewer must display all of these images on the browser,
    we pre-process them to JPEG formats. This allows us to also
    compress the files for efficient dissemination. Furthermore, since
    the images are likely to be high-resolution biological images, we
    decompose the images into image tiles. See `processing/README.md`
    for further details.

* **Image Viewer** This is a web application that provides the
    interface for viewing the image tiles, and to control them. It
    consist of relevant web services for retrieving image meta-data
    and an embeddable Javascript client. See `viewer/README.md` for
    further details.

* **Image database** This is the database that links the image tiles
    to the data contexts. The web services provide an interface for
    accessing this database, which provides the mechanisms for
    retrieving image tiles. See `processing/phenodcc_media.sql` for
    further details.
