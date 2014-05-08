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
import shutil
import urllib2
from contextlib import closing
from urlparse import urlparse
import paramiko
import os
import re
import hashlib
import ConfigParser
from subprocess import call
from PIL import Image

# Hashing block size
HASH_BLOCK_SIZE = 65536

# MySQL statements
GET_CREDENTIAL = '''select protocol_id, hostname, username,
    accesskey, base_path from file_source where centre_id = %s'''

GET_FILES_TO_DOWNLOAD = '''select mp.centre_id as cid,
        pi.pipeline_id as lid,
        mp.genotype_id as gid,
        mp.strain_id as sid,
        p.procedure_id as pid,
        q.parameter_id as qid,
        mp.measurement_id as mid,
        mp.value as url
    from
        phenodcc_overviews.measurements_performed as mp,
        phenodcc_overviews.procedure_animal_overview as pao,
        impress.pipeline as pi,
        impress.`procedure` as p,
        impress.parameter as q
    where
        (mp.measurement_type = 'MEDIAPARAMETER' or
        mp.measurement_type = 'SERIESMEDIAPARAMETERVALUE')
        and mp.procedure_occurrence_id = pao.procedure_occurrence_id
        and pi.pipeline_key = pao.pipeline
        and p.procedure_key = pao.procedure_id
        and q.parameter_key = mp.parameter_id
	and length(substring_index(mp.value, '.', -1)) < 8
    order by cid, lid, gid, sid, pid, qid, mid'''

ADD_FILE_TO_DOWNLOAD = '''insert into phenodcc_media.media_file
    (cid, lid, gid, sid, pid, qid, mid, url, extension_id, is_image, phase_id, status_id, created)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())'''

GET_UNPROCESSED_URL = '''select f.id, cid, lid, gid, sid, pid, qid, url, e.extension as ext
    from phenodcc_media.media_file f, phenodcc_media.file_extension e
    where checksum is null and f.extension_id = e.id
    order by cid, lid, gid, sid, pid, qid, mid, url'''

GET_IMAGE_FILES = '''select id, checksum
    from phenodcc_media.media_file
    where checksum is not null
    and is_image = 1'''

CHECK_IF_CONTEXT_EXISTS = '''select id from phenodcc_media.media_file
    where cid = %s and lid = %s and gid = %s and sid = %s
    and pid = %s and qid = %s and mid = %s'''

CHECK_IF_EXTENSION_EXISTS = 'select id from phenodcc_media.file_extension where extension = %s'
ADD_FILE_EXTENSION = 'insert into phenodcc_media.file_extension (extension) values (%s)'

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


def get_credential(centre_id):
    con = MySQLdb.connect(TRACKER_HOSTNAME,
                          TRACKER_USERNAME,
                          TRACKER_PASSWORD,
                          TRACKER_DATABASE)
    with con:
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_CREDENTIAL, centre_id)
        record = cur.fetchone()
    return record


def download_file(url, dest):
    print "Downloading", url, "and saving as file", dest
    try:
        with closing(urllib2.urlopen(url)) as r:
            with open(dest, 'wb') as f:
                shutil.copyfileobj(r, f)
    except urllib2.URLError:
        return False
    return True


def get_ftp_file(url, dest, cred):
    loc = "ftp://" + cred["username"] + ":" + cred["accesskey"] + "@" + url.netloc + url.path
    return download_file(loc, dest)


def get_sftp_file(url, dest, cred):
    transport = paramiko.Transport((url.netloc, 22))
    transport.connect(username=cred["username"], password=cred["accesskey"])
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get(url.path, dest)
    sftp.close()
    transport.close()
    return True


def get_file(url, dest, cred):
    if url.scheme == "http":
        return download_file(url.geturl(), dest)
    else:
        if url.scheme == "ftp":
            return get_ftp_file(url, dest, cred)
        else:
            if url.scheme == "sftp":
                return get_sftp_file(url, dest, cred)


def get_filetype(con, url):
    extension_id = 0
    is_image = 0
    matches = re.search(r'.*\.([^.]+)$', url)
    if matches:
        extension = matches.group(1).lower()
        if re.match(r'^(bmp|dcm|jpeg|jpg|png|tif)$', extension):
            is_image = 1
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(CHECK_IF_EXTENSION_EXISTS, extension)
        if cur.rowcount == 0:
            cur.execute(ADD_FILE_EXTENSION, extension)
            extension_id = con.insert_id()
        else:
            extension_id = cur.fetchone()['id']
    return extension_id, is_image


def get_context_media():
    global DOWNLOAD_PHASE, PENDING_STATUS

    tracker_con = MySQLdb.connect(TRACKER_HOSTNAME,
                                  TRACKER_USERNAME,
                                  TRACKER_PASSWORD,
                                  TRACKER_DATABASE)

    media_con = MySQLdb.connect(MEDIA_HOSTNAME,
                                MEDIA_USERNAME,
                                MEDIA_PASSWORD,
                                MEDIA_DATABASE)

    with tracker_con, media_con:
        tracker_cur = tracker_con.cursor(MySQLdb.cursors.DictCursor)
        media_cur = media_con.cursor(MySQLdb.cursors.DictCursor)
        already_cur = media_con.cursor(MySQLdb.cursors.DictCursor)
        tracker_cur.execute(GET_FILES_TO_DOWNLOAD)

        for i in range(tracker_cur.rowcount):
            record = tracker_cur.fetchone()
            cid = record['cid']
            lid = record['lid']
            gid = record['gid']
            sid = record['sid']
            pid = record['pid']
            qid = record['qid']
            mid = record['mid']
            url = record['url']
            already_cur.execute(CHECK_IF_CONTEXT_EXISTS, (
                cid, lid, gid, sid, pid, qid, mid
            ))
            if already_cur.rowcount == 0:
                extension_id, is_image = get_filetype(media_con, url)
                media_cur.execute(ADD_FILE_TO_DOWNLOAD, (
                    cid, lid, gid, sid, pid, qid, mid,
                    url, extension_id, is_image,
                    DOWNLOAD_PHASE, PENDING_STATUS
                ))

def create_media_path(cid, lid, gid, sid, pid, qid):
    path = ORIGINAL_MEDIA_FILES_DIR + str(cid) + '/' + str(lid) + '/' + \
        str(gid) + '/' + str(sid) + '/' + str(pid) + '/' + str(qid) + '/'
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def retrieve_file(con, media_id, url, extension, cred, path):
    global DOWNLOAD_PHASE, CHECKSUM_PHASE, RUNNING_STATUS, PENDING_STATUS, FAILED_STATUS
    cur = con.cursor()
    try:
        cur.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, RUNNING_STATUS, media_id))
        con.commit();
        file_path = path + str(media_id) + '.' + extension
        if os.path.exists(file_path):
            print 'File', file_path, 'exists... skipping'
        else:
            get_file(urlparse(url), file_path, cred)
        cur.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, PENDING_STATUS, media_id))
        con.commit();
    except (RuntimeError, TypeError, NameError):
        cur.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, FAILED_STATUS, media_id))
        con.commit();
        return None
    return file_path


def get_sha1(file_path):
    hasher = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read(HASH_BLOCK_SIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(HASH_BLOCK_SIZE)
    except IOError:
        return None
    return hasher.hexdigest()


def set_checksum(con, media_id, file_path):
    global CHECKSUM_PHASE, TILE_GENERATION_PHASE, RUNNING_STATUS, PENDING_STATUS, FAILED_STATUS
    cur = con.cursor()
    cur.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, RUNNING_STATUS, media_id))
    con.commit();
    sha1 = get_sha1(file_path)
    if sha1:
        cur.execute(UPDATE_CHECKSUM, (sha1, media_id))
        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, PENDING_STATUS, media_id))
        con.commit();
    else:
        cur.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, FAILED_STATUS, media_id))
        con.commit();


def update_image_tile_info(con, media_id, checksum):
    cur = con.cursor()
    cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, RUNNING_STATUS, media_id))
    con.commit();
    path = re.sub(r'(.{4})', '\\1/', checksum, 0, re.DOTALL)
    file_path = IMAGE_TILES_DIR + path + 'original.jpg'
    print file_path
    try:
        img = Image.open(file_path)
        cur.execute(UPDATE_IMAGE_SIZE, img.size + (media_id,))
        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, DONE_STATUS, media_id))
        con.commit();
    except (IOError, EOFError):
        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, FAILED_STATUS, media_id))
        con.commit();
        return False
    return True

# TODO
# Convert the `generate_tiles.sh` to Python. At the moment, we do not update
# the status of the processing phase after a media file has being processed.
# This needs to be changed so that the update happens immediately. 
def generate_image_tiles(con):
    call(['./generate_tiles.sh', ORIGINAL_MEDIA_FILES_DIR, IMAGE_TILES_DIR,
          TILE_SIZES, IMAGE_SCALES])
    cur = con.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(GET_IMAGE_FILES)
    for i in range(cur.rowcount):
        record = cur.fetchone()
        update_image_tile_info(con, record['id'], record['checksum'])


def download_and_process():
    con = MySQLdb.connect(MEDIA_HOSTNAME,
                          MEDIA_USERNAME,
                          MEDIA_PASSWORD,
                          MEDIA_DATABASE)
    centre = -1
    cred = None
    with con:
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_UNPROCESSED_URL)
        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            temp = record['cid']
            if centre != temp:
                centre = temp
                cred = get_credential(centre)
            path = create_media_path(record['cid'], record['lid'],
                                     record['gid'], record['sid'],
                                     record['pid'], record['qid'])
            file_path = retrieve_file(con, media_id, record['url'], record['ext'], cred, path)
            if file_path:
                set_checksum(con, media_id, file_path)
        generate_image_tiles(con)


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


def get_configuration():
    global TRACKER_DATABASE, TRACKER_HOSTNAME, TRACKER_USERNAME, TRACKER_PASSWORD
    global MEDIA_DATABASE, MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD
    global ORIGINAL_MEDIA_FILES_DIR, IMAGE_TILES_DIR
    global TILE_SIZES, IMAGE_SCALES

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
    TILE_SIZES = config.get('tiling', 'tile_sizes')
    IMAGE_SCALES = config.get('tiling', 'image_scales')

get_configuration()
set_phase_status_ids()
get_context_media()
download_and_process()



# Python packaged to install
# sudo apt-get install python-mysqldb python-imaging
