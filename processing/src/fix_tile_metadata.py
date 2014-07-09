#! /usr/bin/python
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

import MySQLdb
import os
import re
import hashlib
import ConfigParser
from PIL import Image

# Hashing block size
HASH_BLOCK_SIZE = 65536

# Get all of the media files that have been marked for download.
GET_FILES_MARKED_FOR_DOWNLOADED = '''
select f.id as media_id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.url,
    e.extension as ext, f.is_image, f.checksum, f.phase_id, f.status_id
from
    phenodcc_media.media_file f
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
order by f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.mid
'''

GET_PHASE_ID = "select id from phenodcc_media.phase where short_name = %s limit 1"
GET_STATUS_ID = "select id from phenodcc_media.a_status where short_name = %s limit 1"
UPDATE_PHASE_STATUS = 'update phenodcc_media.media_file set phase_id = %s, status_id = %s where id = %s'
UPDATE_CHECKSUM = 'update phenodcc_media.media_file set checksum = %s where id = %s'
UPDATE_IMAGE_SIZE = 'update phenodcc_media.media_file set width = %s, height = %s where id = %s'

# get phases used
DOWNLOAD_PHASE = -1
CHECKSUM_PHASE = -1
TILE_GENERATION_PHASE = -1

# get phase statuses in use
PENDING_STATUS = -1
RUNNING_STATUS = -1
DONE_STATUS = -1
FAILED_STATUS = -1


# Create file path for saving the downloaded file locally. Since the
# media downloader wishes to archive all of the files that have been
# downloaded, it follows a specific structure.
def create_media_path(cid, lid, gid, sid, pid, qid):
    path = ORIGINAL_MEDIA_FILES_DIR + str(cid) + '/' + str(lid) + '/' + \
           str(gid) + '/' + str(sid) + '/' + str(pid) + '/' + str(qid) + '/'
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# Calculate the SHA1 checksum of the file that was successfully downloaded.
# Note that this checksum is used to link file to their thumbnails and tiles.
def get_sha1(file_path):
    has_generator = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read(HASH_BLOCK_SIZE)
            while len(buf) > 0:
                has_generator.update(buf)
                buf = f.read(HASH_BLOCK_SIZE)
    except IOError:
        return None
    return has_generator.hexdigest()


# Determine width and height of an image file
def get_image_size(image_file):
    size = None
    if os.path.isfile(image_file):
        try:
            img = Image.open(image_file)
            size = img.size
        except (IOError, EOFError):
            print 'Failed to open file', image_file
    return size


# Determine the width and height of the original image in pixels
def get_image_width_height(tiles_path, tile_size):
    # See if the converted original JPEG file still exists.
    # For later versions of the tile generation script, the original will be available.
    size = get_image_size(tiles_path + 'original.jpg')

    if size is None:
        # If we do not have the original converted file, we will have to do some more work
        # to determine the width and height from the tiles for 100% scale.
        original_scale_tiles_path = tiles_path + tile_size + '/100/'
        try:
            for tile in os.listdir(original_scale_tiles_path):
                # Every tile contains the number of columns and rows in the tile grid.
                # We use this information to determine the width and height of the original media.
                if tile.endswith('.jpg'):
                    temp = tile.split('_')
                    num_columns = temp[0]
                    num_rows = temp[1]
                    c = int(num_columns) - 1
                    r = int(num_rows) - 1

                    # Get the size of the bottom-right tile in the tile grid
                    bottom_right_tile_size = get_image_size(original_scale_tiles_path + '/'
                                                            + num_columns + '_' + num_rows + '_'
                                                            + str(r) + '_' + str(c) + '.jpg')
                    if bottom_right_tile_size is not None:
                        tile_size = int(tile_size)
                        size = (tile_size * c + bottom_right_tile_size[0],
                                tile_size * r + bottom_right_tile_size[1])
                        break
        except (OSError):
            print 'Tiles directory', original_scale_tiles_path, 'does not exist'
    return size


# Fix data context associated with media files that have been marked for download.
def fix_marked_files():
    connection = MySQLdb.connect(MEDIA_HOSTNAME,
                                 MEDIA_USERNAME,
                                 MEDIA_PASSWORD,
                                 MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_FILES_MARKED_FOR_DOWNLOADED)
        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['media_id']

            # Get path for systematically storing the original media file that will be downloaded.
            path = create_media_path(record['cid'], record['lid'],
                                     record['gid'], record['sid'],
                                     record['pid'], record['qid'])
            original_media = path + record['media_id'] + '.' + record['ext']
            checksum = get_sha1(original_media)
            if checksum is None:
                # Try to download the file again unless it failed in previous attempt
                if not (record['phase_id'] == DOWNLOAD_PHASE and record['status_id'] == FAILED_STATUS):
                    cur.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, PENDING_STATUS, media_id))
            else:
                cur.execute(UPDATE_CHECKSUM, (checksum, media_id))

                # If media file is not an image, we are done
                if record['is_image'] == 0:
                    cur.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, DONE_STATUS, media_id))
                else:
                    # See if we managed to generate the tiles
                    checksum_path = re.sub(r'(.{4})', '\\1/', checksum, 0, re.DOTALL)
                    tiles_path = IMAGE_TILES_DIR + checksum_path
                    image_size = get_image_width_height(tiles_path, TILE_SIZE)
                    if image_size is None:
                        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, FAILED_STATUS, media_id))
                    else:
                        cur.execute(UPDATE_IMAGE_SIZE, image_size + (media_id,))
                        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, DONE_STATUS, media_id))
            connection.commit()


# Get primary key identifiers from phase and status short names.
def set_phase_status_ids():
    global DOWNLOAD_PHASE, CHECKSUM_PHASE, TILE_GENERATION_PHASE, \
        PENDING_STATUS, RUNNING_STATUS, DONE_STATUS, FAILED_STATUS

    con = MySQLdb.connect(MEDIA_HOSTNAME,
                          MEDIA_USERNAME,
                          MEDIA_PASSWORD,
                          MEDIA_DATABASE)

    with con:
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_PHASE_ID, "download")
        DOWNLOAD_PHASE = cur.fetchone()['id']
        cur.execute(GET_PHASE_ID, "checksum")
        CHECKSUM_PHASE = cur.fetchone()['id']
        cur.execute(GET_PHASE_ID, "tile")
        TILE_GENERATION_PHASE = cur.fetchone()['id']
        cur.execute(GET_STATUS_ID, "pending")
        PENDING_STATUS = cur.fetchone()['id']
        cur.execute(GET_STATUS_ID, "running")
        RUNNING_STATUS = cur.fetchone()['id']
        cur.execute(GET_STATUS_ID, "done")
        DONE_STATUS = cur.fetchone()['id']
        cur.execute(GET_STATUS_ID, "failed")
        FAILED_STATUS = cur.fetchone()['id']


# Get database and execution details from configuration file.
def get_configuration():
    global TRACKER_DATABASE, TRACKER_HOSTNAME, TRACKER_USERNAME, TRACKER_PASSWORD
    global MEDIA_DATABASE, MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD
    global ORIGINAL_MEDIA_FILES_DIR, IMAGE_TILES_DIR
    global TILE_SIZE, IMAGE_SCALES

    config = ConfigParser.RawConfigParser()
    config.read('phenodcc_media.config')

    TRACKER_DATABASE = config.get('tracker', 'database')
    TRACKER_HOSTNAME = config.get('tracker', 'hostname')
    TRACKER_USERNAME = config.get('tracker', 'username')
    TRACKER_PASSWORD = config.get('tracker', 'password')

    MEDIA_DATABASE = config.get('media', 'database')
    MEDIA_HOSTNAME = config.get('media', 'hostname')
    MEDIA_USERNAME = config.get('media', 'username')
    MEDIA_PASSWORD = config.get('media', 'password')

    # Directory where media files should be downloaded
    # and where the generated images tiles should go
    ORIGINAL_MEDIA_FILES_DIR = config.get('dirs', 'originals_dir')
    if not ORIGINAL_MEDIA_FILES_DIR.endswith('/'):
        ORIGINAL_MEDIA_FILES_DIR += '/'

    IMAGE_TILES_DIR = config.get('dirs', 'tiles_dir')
    if not IMAGE_TILES_DIR.endswith('/'):
        IMAGE_TILES_DIR += '/'

    # Concerning tile generation
    TILE_SIZE = config.get('tiling', 'tile_size')
    IMAGE_SCALES = config.get('tiling', 'image_scales')


get_configuration()
set_phase_status_ids()
fix_marked_files()



# Python packaged to install
# sudo apt-get install python-mysqldb python-imaging
