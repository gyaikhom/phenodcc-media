#! /bin/bash
#
# Copyright 2014 Medical Research Council Harwell.
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

# Prepare the visualisation component
echo "    Compressing Javascript...";
java -jar yuicompressor-2.4.7.jar -o js/imageviewer.DCC_IMAGEVIEWER_VERSION.js js/imageviewer.js;

# Now combine all of the Javascripts into one application.
echo "    Combining Javascripts to a single application...";
cat js/d3.v3.min.js js/imageviewer.DCC_IMAGEVIEWER_VERSION.js > js/app.DCC_IMAGEVIEWER_VERSION.js;
rm -Rf js/d3.v3.min.js js/imageviewer.js js/imageviewer.DCC_IMAGEVIEWER_VERSION.js;

# Now prepare the style sheets, and combine them.
echo "    Compression style sheets...";
java -jar yuicompressor-2.4.7.jar -o css/imageviewer.DCC_IMAGEVIEWER_VERSION.css css/imageviewer.css;
rm -Rf css/imageviewer.css;

echo "    Generating documentation...";
cd doc;
./prepare.sh;
cd ..;
cp doc/manual.html .;
rm -Rf doc;
