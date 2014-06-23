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

# Generates toolbar icons using different hue, brightness and contrasts.
on_bc=$1;
off_bc=$2;
colour=$3;

# set hue for 'on' icons
if [ -z $colour ]
then
    echo "Hue for 'on' icons not supplied: using rgb(255,75,0)";
    colour='rgb(239,123,11)';
else
    echo "Hue for 'on' icons: $colour";
fi

# set brightness-contrast for 'on' icons
if [ -z $on_bc ]
then
    echo "brightness-contrast value for 'on' icons not supplied: using 10";
    on_bc=10;
else
    echo "brightness-contrast value for 'on' icons: ${on_bc}";
fi

# set brightness-contrast for 'off' icons
if [ -z $off_bc ]
then
    echo "brightness-contrast value for 'off' icons not supplied: using 80";
    off_bc=80;
else
    echo "brightness-contrast value for 'off' icons: ${off_bc}";
fi

for x in `ls *.png`;
do
    f=`basename $x .png`;
    convert ${f}.png -brightness-contrast $off_bc ../${f}_off.png;
    convert ${f}.png -type TrueColorMatte -define png:color-type=6 +level-colors ${colour}, -brightness-contrast $on_bc ../${f}_on.png;
done;

