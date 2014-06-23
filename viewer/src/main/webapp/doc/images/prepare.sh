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

# Generate documentation images from Google Chrome screenshots.
rm -Rf shadowed resized;
mkdir shadowed resized;

for x in `ls raw/*.png`;
do
    echo Preparing $x ...;
    fn=`basename $x`;
    convert $x -crop +4+77 -crop -4-4 cropped.png;
    convert cropped.png \( +clone -background '#ddd' -shadow 80x3-6-0 \) +swap -background white \
        \( +clone -background '#ddd' -shadow 80x3-0-6 \) +swap -background white \
        \( +clone -background '#ddd' -shadow 80x3+6+0 \) +swap -background white \
        \( +clone -background '#ddd' -shadow 80x3+0+6 \) +swap -background white \
        -layers merge +repage shadowed/${fn};
    convert shadowed/${fn} -resize 60% -unsharp 1 resized/${fn};
done;

rm -f cropped.png;
