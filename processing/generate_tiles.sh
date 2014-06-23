#! /bin/bash
#
# Copyright 2013 Medical Research Council Harwell.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
#

# This program generates a well organised set of tiles from the user
# supplied directory of images.

# Semantic version
version="0.1";

# Preferred image format
pref_format="jpg";

# Source directory for the images.
dir_src=$1;

# Destination directory for tiles images.
dir_dest=$2;

# Comma separated tile sizes to generate tiles set for
# E.g., 128,256
tile_sizes=$3

# Comma separated image scales to generate tiles set for
# E.g., 10,25,50,75,100
image_scales=$4

case `uname -s` in
    Darwin)
        sha_cmd="shasum";
        ;;
    *)
        sha_cmd="sha1sum";
        ;;
esac


function generate_tiles() {
    # Uses ImageMagick to generate tiles
    (cd $1; convert scaled.${extension} -crop $2x$2 -set filename:tile "%[fx:ceil(page.width/$2)]_%[fx:ceil(page.height/$2)]_%[fx:page.y/$2]_%[fx:page.x/$2]" +repage +adjoin "%[filename:tile].$extension"; )
}

# Scales the original image and then generates the tiles
#
# @param $1 Directory that contains the image
# @param $2 Maximum size of a tile in pixels
# @param $3 Scale in percentage
#
# E.g., scale_and_generate_tiles b5eaf5627beae587bc779b68ec8f41b30caa4015 64 80
# will first scale the image by 80% and then generate tiles where each
# tile is smaller or equal to 64x64.
function scale_and_generate_tiles() {
    tiles_dir=$1$2/$3;
    if [ ! -d "tiles_dir" ]
    then
        #echo "    Directory $tiles_dir for $2x$2 tiles at $3% scale does not exists...";
        mkdir -p ${tiles_dir};
    fi;
    
    # Uses ImageMagick to scale the image
    if [ ! -z "$3" ]
    then
        (cd ${tiles_dir}; convert ../../original.${extension} -resize $3% scaled.${extension}; )
    fi;

    generate_tiles ${tiles_dir} $2;
}

# Generates tile set from an original image using supplied tile sizes
# at supplied scales.
#
# @param $1 Directory that contains the image
# @param $2 Comma separate list of maximum sizes of tiles in pixels
# @param $3 Comma separated list of scales in percentage
function generate_tiles_set() {
    checksum_dir=$1;

    if [ "$extension" = "dcm" ]
    then
        #echo "    Converting DICOM to preferred image format...";
        (cd ${checksum_dir}; convert -define dcm:display-range=reset original.${extension} -normalize original.${pref_format}; )
    else
        #echo "    Converting image to preferred image format...";
        (cd ${checksum_dir}; convert original.${extension} original.${pref_format}; )
    fi;

    # we convert all images to preferred image format before processing
    extension="$pref_format";

    # If there were multiple extracted files generated (e.g., TIF), choose
    # the largest file as original image.
    #
    # NOTE: we are assuming TIF files may contain the same image at
    # different zooms; but not different images.
    if [ `find ${checksum_dir} -iname "*.${pref_format}" -type f | wc -l` -gt 1 ]
    then
        largest_file=`find ${checksum_dir} -iname "*.${pref_format}" -type f -print0 | xargs -0 du -b | sort -nr | head -n 1 | cut -f 2`;
        mv ${largest_file} ${checksum_dir}original.${pref_format};
        
        # Delete all of the other extracted images
        find ${checksum_dir} ! -iname "original.${pref_format}" -type f -delete;
    fi;

    #echo "    Generating thumbnail...";
    (cd ${checksum_dir}; convert original.${pref_format} -resize 300x thumbnail.${pref_format}; )

    echo "$2" | sed -n 1'p' | tr ',' '\n' |
    while read tile_size;
    do
        #echo "    Generating ${tile_size} x ${tile_size} tiles...";
        echo "$3" | sed -n 1'p' | tr ',' '\n' |
        while read scale;
        do
            #echo "    Generating tiles at scale $scale%...";
            scale_and_generate_tiles ${checksum_dir} ${tile_size} ${scale};
        done;
    done;
}

echo "----------------------------------------------------------------";
echo "TILED IMAGE GENERATOR";
echo "Version $version";
echo "The International Mouse Phenotyping Consortium";
echo "http://www.mousephenotype.org/";
echo "----------------------------------------------------------------";

if [ ! $# -eq 4 ]
then
    echo "Usage:";
    echo "    generate_tiles <source> <destination> <sizes> <scales>";
    echo "";
    echo " E.g., generate_tiles sample tiles 128,256 50,100";
    echo "";
    echo " source - Source directory that contains image files to process.";
    echo " destination - Destination directory to store image tiles set.";
    echo " sizes - Comma separated list of tile sizes (in pixels).";
    echo " scales - Comma separated list of scales (in percentage).";
    exit 1;
fi;

echo "     Source: ${dir_src}";
echo "Destination: ${dir_dest}";
echo "-----------------------------------------------------------";

if [ ! -d ${dir_src} ]
then
    echo "ERROR: Supplied image source directory does not exists...";
    echo "Will abort image tile generation...";
    exit 1;
fi;

if [ ! -d ${dir_dest} ]
then
    echo "Supplied target directory does not exists...";
    echo "    Creating directory...";
    mkdir -p ${dir_dest};
fi;

total_files=0;
for file in `find ${dir_src} -type f -regex ".*\.\(bmp\|dcm\|jpeg\|jpg\|png\|tif\)"`;
do
    echo "Processing $file...";

    basename=$(basename "${file}");
    extension="${file##*.}";
    filename=`basename ${basename} .${extension}`;
    #echo "    Basename: ${basename}";
    #echo "    Filename: ${filename}";
    #echo "    Extension: ${extension}";

    checksum=`${sha_cmd} ${file} | cut -d " " -f 1`;
    #echo "    Checksum: ${checksum}";

    # We could just use the checksum, but the number of directories
    # in this flat representation could reach the filesystem limit.
    # Furthermore, this could slow down the filesystem. We therefore
    # break down the checksum into buckets, where each bucket is
    # four characters long, so that the bucket hierarchy depth is ten.
    # Hence, at each level, we can have 65536 (16^4) items.
    #
    # E.g., we get the directory from

    # b5eaf5627beae587bc779b68ec8f41b30caa4015
    #
    # as
    #
    # b5ea/f562/7bea/e587/bc77/9b68/ec8f/41b3/0caa/4015
    #
    checksum_hierarchy=`echo ${checksum} | sed 's/.\{4\}/&\//g'`
    #echo ${checksum_hierarchy};
    checksum_dir=${dir_dest}${checksum_hierarchy};
    checksum_filepath=${checksum_dir}original.${extension};

    if [ ! -d "${checksum_dir}" ]
    then
        #echo "    Directory ${checksum_dir} does not exists...";
        mkdir -p ${checksum_dir};
    fi;

    if [ -e "${checksum_filepath}" ]
    then
        echo "    File ${checksum_filepath} already exists... skipping";
    else
        #echo "    Creating ${checksum_filepath}...";
        cp -f ${file} ${checksum_filepath};
        
        generate_tiles_set ${checksum_dir} ${tile_sizes} ${image_scales};
    fi;

    let total_files++;
done;


echo "----------------------------------------------------------------";
echo "Total files processed: $total_files";
echo "----------------------------------------------------------------";
