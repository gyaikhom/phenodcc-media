#! /usr/bin/python
#
# Copyright 2014 Medical Research Council Harwell.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
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

import ConfigParser
import MySQLdb
import getopt
import os
import re
import shutil
import urllib2
from contextlib import closing
from urlparse import urlparse
import paramiko
import hashlib
import sys
from subprocess import call
from PIL import Image
import fcntl
import time
from datetime import datetime

VERSION = '0.7.3'
HASH_BLOCK_SIZE = 65536
MAX_DOWNLOAD_RETRIES = 3
SLEEP_SECS_BEFORE_RETRY = 20  # 20 seconds

verbose = False

# sys.stdout.flush() is used everywhere there is a print
# There doesn't seem to be a standard approach for doing this.
#
# 1) python -u
# 2) Opening the stdout as flushing
# 3) Using flush = true in print (available only on 3.3)
# 4) Setting env, etc.
#
# Can't be bothered... Using the C way of doing things

LOG_ERROR = '''
insert into phenodcc_media.error_logs
(media_id, phase_id, error_msg, created)
values (%s, %s, %s, now())
'''

GET_MEDIA_FILES = '''
select mp.centre_id as cid,
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
    (mp.measurement_type = 'MEDIAPARAMETER' or mp.measurement_type = 'SERIESMEDIAPARAMETERVALUE')
    and mp.procedure_occurrence_id = pao.procedure_occurrence_id
    and pi.pipeline_key = pao.pipeline
    and p.procedure_key = pao.procedure_id
    and q.parameter_key = mp.parameter_id
    and length(substring_index(mp.value, '.', -1)) < 8
order by cid, lid, gid, sid, pid, qid, mid
'''

ADD_FILE_TO_DOWNLOAD = '''
insert into phenodcc_media.media_file
(cid, lid, gid, sid, pid, qid, mid, url, extension_id, is_image, phase_id, status_id, created)
values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
'''

# Note that many resubmissions might be happening, which should all point to
# the first successful download. This is why we order them in ascending order by
# the id (because lower ids are the oldest entries) and limit result by one.
# We are only interested in successful downloads (i.e., phase > download)
CHECK_IF_URL_ALREADY_DOWNLOADED = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension
from phenodcc_media.media_file as f
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where f.phase_id > 1 and f.url = %s
order by id asc
limit 1
'''

CHECK_IF_FILE_ALREADY_EXISTS = '''
select id from phenodcc_media.media_file
where cid = %s and lid = %s and gid = %s and sid = %s and pid = %s and qid = %s and mid = %s
'''

CHECK_IF_EXTENSION_EXISTS = "select id from phenodcc_media.file_extension where extension = %s"
ADD_FILE_EXTENSION = "insert into phenodcc_media.file_extension (extension) values (%s)"

GET_CREDENTIAL = '''
select protocol_id, hostname, username, accesskey, base_path from file_source where centre_id = %s
'''

GET_FILES_TO_BE_DOWNLOADED = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.url, e.extension
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where p.short_name = "download" and s.short_name = "pending"
order by f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.mid, f.url
'''

GET_IMAGE_FILES_TO_TILE = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where f.is_image = 1 and f.checksum is not null and p.short_name = "checksum" and s.short_name = "done"
order by f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.mid
'''

GET_INTERRUPTED_DOWNLOADS = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where p.short_name = "download" and s.short_name = "running"
'''

GET_INTERRUPTED_CHECKSUM = '''
select f.id
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
where
    (p.short_name = "checksum" and s.short_name = "running")
    or (p.short_name = "download" and s.short_name = "done")
'''

GET_INTERRUPTED_TILING = '''
select f.id, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
where p.short_name = "tile" and s.short_name = "running"
'''

GET_TILING_DONE = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where p.short_name = "tile" and s.short_name = "done"
order by f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.mid
'''

GET_PHASE_ID = "select id from phenodcc_media.phase where short_name = %s limit 1"
GET_STATUS_ID = "select id from phenodcc_media.a_status where short_name = %s limit 1"
UPDATE_PHASE_STATUS = "update phenodcc_media.media_file set phase_id = %s, status_id = %s where id = %s"
UPDATE_CHECKSUM = "update phenodcc_media.media_file set checksum = %s where id = %s"
UPDATE_IMAGE_SIZE = "update phenodcc_media.media_file set width = %s, height = %s where id = %s"

# get phases used
DOWNLOAD_PHASE = -1
CHECKSUM_PHASE = -1
TILE_GENERATION_PHASE = -1

# get phase statuses in use
PENDING_STATUS = -1
RUNNING_STATUS = -1
DONE_STATUS = -1
FAILED_STATUS = -1

# global variables
TRACKER_HOSTNAME = TRACKER_USERNAME = TRACKER_PASSWORD = TRACKER_DATABASE = \
    MEDIA_HOSTNAME = MEDIA_USERNAME = MEDIA_PASSWORD = MEDIA_DATABASE = \
    ORIGINAL_MEDIA_FILES_DIR = IMAGE_TILES_DIR = TILE_SIZE = IMAGE_SCALES = None


def get_media_storage_path(centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id):
    return ORIGINAL_MEDIA_FILES_DIR + str(centre_id) + '/' + str(pipeline_id) + '/' + \
           str(genotype_id) + '/' + str(strain_id) + '/' + str(procedure_id) + '/' + str(parameter_id) + '/'


def get_original_media_path(centre_id, pipeline_id, genotype_id, strain_id,
                            procedure_id, parameter_id, media_id, file_extension):
    base_path = get_media_storage_path(centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id)
    return base_path + str(media_id) + '.' + file_extension


def create_media_storage_path(centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id):
    path = get_media_storage_path(centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def log_error(connection, media_id, phase_id, error_msg):
    modify = connection.cursor()
    modify.execute(LOG_ERROR, (media_id, phase_id, error_msg))
    connection.commit()


# Get the consistent unique identifiers for the phases and statuses
def set_phase_status_ids():
    global DOWNLOAD_PHASE, CHECKSUM_PHASE, TILE_GENERATION_PHASE, \
        PENDING_STATUS, RUNNING_STATUS, DONE_STATUS, FAILED_STATUS

    con = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
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


# Get configuration from the supplied config file
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


# Returns a tuple that determines the file type
# 1) The file extension, and
# 2) A boolean value that is true if the file is an image; false, otherwise.
def get_file_type(con, url):
    extension_id = 0
    is_image = 0
    matches = re.search(r'.*\.([^.]+)$', url)

    if matches:
        extension = matches.group(1).lower()
        print 'match:', url, extension
        sys.stdout.flush()

        if re.match(r'^(bmp|dcm|jpeg|jpg|png|tif|tiff)$', extension):
            is_image = 1
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(CHECK_IF_EXTENSION_EXISTS, extension)
        if cur.rowcount == 0:
            cur.execute(ADD_FILE_EXTENSION, extension)
            con.commit()
            extension_id = con.insert_id()
        else:
            extension_id = cur.fetchone()['id']
    else:
        print 'no match:', url
        sys.stdout.flush()

    return extension_id, is_image


# Adds a URL into the list of files to be downloaded and processed
# Note that the actual downloading and processing of the files are
# handled by a different process. This prevents the download and
# processing of files from blocking the crawler.
def add_files_to_download():
    tracker_connection = MySQLdb.connect(TRACKER_HOSTNAME, TRACKER_USERNAME, TRACKER_PASSWORD, TRACKER_DATABASE)
    media_connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with tracker_connection, media_connection:
        tracker_cur = tracker_connection.cursor(MySQLdb.cursors.DictCursor)
        media_cur = media_connection.cursor(MySQLdb.cursors.DictCursor)
        already_cur = media_connection.cursor(MySQLdb.cursors.DictCursor)
        tracker_cur.execute(GET_MEDIA_FILES)

        if verbose and tracker_cur.rowcount > 0:
            print tracker_cur.rowcount, 'media files found...'
            sys.stdout.flush()

        to_download = 0
        already_downloaded = 0
        for i in range(tracker_cur.rowcount):
            record = tracker_cur.fetchone()
            centre_id = record['cid']
            pipeline_id = record['lid']
            genotype_id = record['gid']
            strain_id = record['sid']
            procedure_id = record['pid']
            parameter_id = record['qid']
            measurement_id = record['mid']
            url_to_download = record['url']

            # We ignore files that have already been processed, or is
            # mark for processing. We do this to avoid race condition.
            # This script is run by the crawler, and the download and
            # processing is run by a different process. Since download
            # and processing only works on files that are already marked,
            # restricting this script to additions prevents a race.
            already_cur.execute(CHECK_IF_FILE_ALREADY_EXISTS, (
                centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id, measurement_id
            ))
            if already_cur.rowcount == 0:
                extension_id, is_image = get_file_type(media_connection, url_to_download)
                media_cur.execute(ADD_FILE_TO_DOWNLOAD, (
                    centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id, measurement_id,
                    url_to_download, extension_id, is_image, DOWNLOAD_PHASE, PENDING_STATUS
                ))
                media_connection.commit()
                to_download += 1
                if verbose:
                    print '    Url', url_to_download, 'has been added for download and processing...'
                    sys.stdout.flush()
            else:
                already_downloaded += 1

        if verbose:
            print '    ', already_downloaded, 'media files already downloaded...'
            print '    ', to_download, 'new media files added to download queue...'
            sys.stdout.flush()


# Get credentials to access the file servers from where to download the images.
def get_credential(centre_id):
    con = MySQLdb.connect(TRACKER_HOSTNAME, TRACKER_USERNAME, TRACKER_PASSWORD, TRACKER_DATABASE)
    with con:
        cur = con.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_CREDENTIAL, centre_id)
        record = cur.fetchone()
    if record['accesskey'] == '':
        record['accesskey'] = None
    return record


# Download the file from the supplied URL and save it to destination file.
def download_file(url, save_as, max_attempts):
    if verbose:
        print "Downloading", url, "and saving as file", save_as
        sys.stdout.flush()
    num_retries = 1
    while num_retries <= max_attempts:
        if verbose:
            print "    Attempt", num_retries,
            sys.stdout.flush()
        try:
            with closing(urllib2.urlopen(url)) as r:
                with open(save_as, 'wb') as f:
                    shutil.copyfileobj(r, f)
            if verbose:
                print " [ SUCCESS ]"
                sys.stdout.flush()
            return
        except (urllib2.URLError, IOError) as e:
            if verbose:
                print "[ FAIL ]"
                print "        ERROR: download_file -", e
                sys.stdout.flush()
            num_retries += 1
            if num_retries > max_attempts:
                if verbose:
                    print "    [ Giving up the download, maximum retries reached ]"
                    sys.stdout.flush()
                raise e
            else:
                if verbose:
                    print "    [ Sleeping for", SLEEP_SECS_BEFORE_RETRY / 60, "minutes before re-attempt ]"
                    sys.stdout.flush()
                time.sleep(SLEEP_SECS_BEFORE_RETRY)


# Download file from a FTP server using the supplied credentials.
def get_ftp_file(url, save_as, cred):
    try:
        loc = "ftp://"
        # temporary hack to proceed with anonymous download if processing Jax
        if cred["username"] != 'jlkexternal':
            loc = loc + cred["username"] + ":" + cred["accesskey"] + "@"
        loc = loc + url.netloc + url.path
        download_file(loc, save_as, MAX_DOWNLOAD_RETRIES)
    except (urllib2.URLError, IOError) as e:
        if verbose:
            print "  ! Download with username/password failed:", e.strerror
            print "    [ Will attempt anonymous download ]"
            sys.stdout.flush()
        try:
            loc = "ftp://" + url.netloc + url.path
            download_file(loc, save_as, 1)  # To prevent incorrect login IP band, try only once
        except (urllib2.URLError, IOError):
            raise e  # We wish to record the first exception (as that is the expected one)


# Download file from a sFTP server using the supplied credentials.
def get_sftp_file(url, save_as, cred):
    if verbose:
        print "Downloading", url, "and saving as file", save_as
        sys.stdout.flush()
    num_retries = 1
    while num_retries <= MAX_DOWNLOAD_RETRIES:
        if verbose:
            print "    Attempt", num_retries,
            sys.stdout.flush()
        try:
            pkey = paramiko.RSAKey.from_private_key_file('/home/dcccrawler/.ssh/id_rsa')
            transport = paramiko.Transport((url.netloc.split(':')[0], 22))
            transport.connect(username=cred["username"], password=cred["accesskey"], pkey=pkey)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(url.path, save_as)
            sftp.close()
            transport.close()
            if verbose:
                print "[ SUCCESS ]"
                sys.stdout.flush()
            return
        except (IOError, paramiko.PasswordRequiredException, paramiko.SSHException) as e:
            if verbose:
                print "[ FAIL ]"
                print "        ERROR: get_sftp_file -", e
                sys.stdout.flush()
            num_retries += 1
            if num_retries > MAX_DOWNLOAD_RETRIES:
                if verbose:
                    print "    [ Giving up the download, maximum retries reached ]"
                    sys.stdout.flush()
                raise e
            else:
                if verbose:
                    print "    [ Sleeping for", SLEEP_SECS_BEFORE_RETRY / 60, "minutes before re-attempt ]"
                    sys.stdout.flush()
                time.sleep(SLEEP_SECS_BEFORE_RETRY)


# Download file from the file server using the supplied credential.
def get_file(url_to_download, save_as, cred):
    # make the supplied url safe for download
    url = urlparse(urllib2.quote(url_to_download, safe="%/:=&?~#+!$,;'@()*[]"))

    if url.scheme == "http" or url.scheme == "https":
        download_file(url.geturl(), save_as, MAX_DOWNLOAD_RETRIES)
    elif url.scheme == "ftp":
        get_ftp_file(url, save_as, cred)
    elif url.scheme == "sftp":
        get_sftp_file(url, save_as, cred)
    else:
        raise urllib2.URLError("Unsupported internet transport protocol: " + url.scheme)


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
    except IOError as e:
        if verbose:
            print "get_sha1 -", e
            sys.stdout.flush()
        return None
    return has_generator.hexdigest()


# Set the checksum of the media file record by calculating the SHA1 checksum of the downloaded file.
def set_checksum(connection, media_id, file_saved_as):
    modify = connection.cursor()
    modify.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, RUNNING_STATUS, media_id))
    connection.commit()
    sha1 = get_sha1(file_saved_as)
    if sha1 is None:
        modify.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, FAILED_STATUS, media_id))
    else:
        modify.execute(UPDATE_CHECKSUM, (sha1, media_id))
        modify.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, DONE_STATUS, media_id))
    connection.commit()
    return sha1


# First check if the URL was already downloaded successfully. This happens when 
# centres resubmit the same URLs, and because new measurement ids are assigned,
# the same URL is marked as a new media file. Since downloading files is
# really expensive in terms of bandwidth and storage space, we try to optimise this
# by instead creating a symbolic link to the existing file.
def check_and_download(connection, url_to_download, file_save_as, credentials):
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(CHECK_IF_URL_ALREADY_DOWNLOADED, url_to_download)

    if cur.rowcount == 0:
        get_file(url_to_download, file_save_as, credentials)
    else:
        record = cur.fetchone()
        media_id = record['id']
        centre_id = record['cid']
        pipeline_id = record['lid']
        genotype_id = record['gid']
        strain_id = record['sid']
        procedure_id = record['pid']
        parameter_id = record['qid']
        file_extension = record['extension']

        existing_file = get_original_media_path(centre_id, pipeline_id,
                                                genotype_id, strain_id,
                                                procedure_id, parameter_id,
                                                media_id, file_extension)
        try:
            # Create relative symlink
            src_split = os.path.split(file_save_as)
            os.symlink(os.path.relpath(existing_file, src_split[0]), file_save_as)
        except OSError:
            # If we cannot create a symlink, probably the file is no longer
            # there. So, just re-download it again.
            if verbose:
                print "    Failed to create symbolic link to:", existing_file
                print "    [ Will download as a new file ]"
                sys.stdout.flush()
            get_file(url_to_download, file_save_as, credentials)


# Download file that has not been downloaded and update download status.
# connection - Connection to use for accessing the database
# media_id - Primary key of the record associated with the file
# credentials - Credentials for accessing the file server
# url_to_download - URL to download
# file_save_as - Where to save the file once downloaded
def retrieve_file(connection, media_id, credentials, url_to_download, file_save_as):
    download_successful = False
    if os.path.exists(file_save_as):
        print 'File', file_save_as, 'already exists... will skip'
        sys.stdout.flush()
        download_successful = True
    else:
        modify = connection.cursor()
        try:
            modify.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, RUNNING_STATUS, media_id))
            connection.commit()
            check_and_download(connection, url_to_download, file_save_as, credentials)
            modify.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, PENDING_STATUS, media_id))
            connection.commit()
            download_successful = True
        except (MySQLdb.Error, OSError, IOError, urllib2.URLError,
                paramiko.PasswordRequiredException, paramiko.SSHException) as e:
            modify.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, FAILED_STATUS, media_id))
            connection.commit()
            log_error(connection, media_id, DOWNLOAD_PHASE, repr(e))
    return download_successful


# Download media files.
def download_media():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    centre = -1
    credentials = None
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_FILES_TO_BE_DOWNLOADED)

        if verbose and cur.rowcount > 0:
            print 'Downloading', cur.rowcount, 'media files...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            centre_id = record['cid']
            pipeline_id = record['lid']
            genotype_id = record['gid']
            strain_id = record['sid']
            procedure_id = record['pid']
            parameter_id = record['qid']
            url_to_download = record['url']
            file_extension = record['extension']

            # this assumes that all of the media files for a centre are processed in groups.
            # See the ordering in GET_FILES_TO_BE_DOWNLOADED.
            if centre != centre_id:
                centre = centre_id
                credentials = get_credential(centre)

            # Get path for systematically storing the original media file that will be downloaded.
            create_media_storage_path(centre_id, pipeline_id, genotype_id, strain_id, procedure_id, parameter_id)
            file_save_as = get_original_media_path(centre_id, pipeline_id, genotype_id, strain_id,
                                                   procedure_id, parameter_id, media_id, file_extension)
            download_successful = retrieve_file(connection, media_id, credentials, url_to_download, file_save_as)
            if download_successful:
                set_checksum(connection, media_id, file_save_as)


# Determine width and height of an image file
def get_image_size(image_file):
    size = None
    if os.path.isfile(image_file):
        try:
            img = Image.open(image_file)
            size = img.size
        except (IOError, EOFError) as e:
            print 'Failed to open file', image_file
            sys.stdout.flush()
            if verbose:
                print "get_image_size -", e
                sys.stdout.flush()

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
        except OSError as e:
            print 'Tiles directory', original_scale_tiles_path, 'does not exist'
            sys.stdout.flush()
            if verbose:
                print "get_image_width_height -", e
                sys.stdout.flush()

    return size


# Update meta-data for the image tiles that have been generated from the original media.
def update_tile_metadata(connection, media_id, image_size):
    cur = connection.cursor()
    if image_size is None:
        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, FAILED_STATUS, media_id))
    else:
        cur.execute(UPDATE_IMAGE_SIZE, image_size + (media_id,))
        cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, DONE_STATUS, media_id))
    connection.commit()


# To work around file system restrictions on the number of items allowed in a
# directory, we do not store the tiles using the file_checksum. Instead, we decompose
# the 40 character file_checksum into a path that is 10 levels deep, where the directory
# name contains four characters.
def get_tile_storage_path(file_checksum):
    return IMAGE_TILES_DIR + re.sub(r'(.{4})', '\\1/', file_checksum, 0, re.DOTALL)


# Generates tiles from the supplied media file for the supplied scales and tile size.
# connection - Connection to use for accessing phenodcc_media
# media_id - Primary key of record associated with the media file
# original_media - File path to the original media file
# checksum - The checksum of the media file that was downloaded
def generate_image_tiles(connection, media_id, original_media, file_checksum):
    if verbose:
        print '    Generating tiles for', original_media
        sys.stdout.flush()

    cur = connection.cursor()
    cur.execute(UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, RUNNING_STATUS, media_id))
    connection.commit()

    # To work around file system restrictions on the number of items allowed in a
    # directory, we do not store the tiles using the file_checksum. Instead, we decompose
    # the 40 character file_checksum into a path that is 10 levels deep, where the directory
    # name contains four characters.
    tiles_path = get_tile_storage_path(file_checksum)

    # Run the script that generates the image tiles.
    return_code = call(['./generate_tiles_for_image.sh', original_media, IMAGE_TILES_DIR, TILE_SIZE, IMAGE_SCALES])
    if return_code == 0:
        update_tile_metadata(connection, media_id, get_image_width_height(tiles_path, TILE_SIZE))
    else:
        update_tile_metadata(connection, media_id, None)
    return return_code


# Generate tiles for all of the image media files.
def generate_tiles():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_IMAGE_FILES_TO_TILE)

        if verbose and cur.rowcount > 0:
            print 'Generating tiles for', cur.rowcount, 'media files...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            centre_id = record['cid']
            pipeline_id = record['lid']
            genotype_id = record['gid']
            strain_id = record['sid']
            procedure_id = record['pid']
            parameter_id = record['qid']
            file_extension = record['extension']
            file_checksum = record['checksum']

            original_media = get_original_media_path(centre_id, pipeline_id, genotype_id, strain_id,
                                                     procedure_id, parameter_id, media_id, file_extension)
            generate_image_tiles(connection, media_id, original_media, file_checksum)


def fix_interrupted_downloads():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        modify = connection.cursor()
        cur.execute(GET_INTERRUPTED_DOWNLOADS)

        if verbose and cur.rowcount > 0:
            print 'Fixing', cur.rowcount, 'interrupted downloads...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            centre_id = record['cid']
            pipeline_id = record['lid']
            genotype_id = record['gid']
            strain_id = record['sid']
            procedure_id = record['pid']
            parameter_id = record['qid']
            file_extension = record['extension']

            if verbose:
                print '    Will re-download media file', media_id
                sys.stdout.flush()

            # If the download was interrupted, any existing file could be corrupted or incomplete.
            # Since the normal downloader skips existing files, we must first delete any existing
            # file so that the media file is downloaded again.
            original_media = get_original_media_path(centre_id, pipeline_id, genotype_id, strain_id,
                                                     procedure_id, parameter_id, media_id, file_extension)
            if original_media and os.path.exists(original_media):
                os.remove(original_media)

            # Now, mark this for re-downloading in the next download run.
            modify.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, PENDING_STATUS, media_id))
            connection.commit()


def fix_interrupted_checksum():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        modify = connection.cursor()
        cur.execute(GET_INTERRUPTED_CHECKSUM)

        if verbose and cur.rowcount > 0:
            print 'Fixing', cur.rowcount, 'interrupted checksum calculations...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']

            if verbose:
                print '    Will re-calculate checksum for media file', media_id
                sys.stdout.flush()

            # Mark this for re-downloading in the next download run.
            # Since only checksum was interrupted, the download must have completed
            # successfully. By not deleting this file, the download phase will be skipped
            # followed by calculation of the checksum as usual.
            modify.execute(UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, PENDING_STATUS, media_id))
            connection.commit()


def fix_interrupted_tiling():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        modify = connection.cursor()
        cur.execute(GET_INTERRUPTED_TILING)

        if verbose and cur.rowcount > 0:
            print 'Fixing', cur.rowcount, 'interrupted media tiling...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            file_checksum = record['checksum']

            if verbose:
                print '    Will re-generate tiles for media file', media_id, 'with checksum', file_checksum
                sys.stdout.flush()

            # If the tiling was interrupted, it is highly likely that the tiles set is
            # incomplete. We therefore need to assume that the worst has happen and
            # re-generate the tiles set all over again. To do this, we must first delete
            # the existing tiles directory.
            tiles_path = get_tile_storage_path(file_checksum)
            if tiles_path and os.path.exists(tiles_path):
                shutil.rmtree(tiles_path)

            # Now, mark this for tile re-generation.
            modify.execute(UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, DONE_STATUS, media_id))
            connection.commit()


def fix_interrupted_phases():
    fix_interrupted_downloads()
    fix_interrupted_checksum()
    fix_interrupted_tiling()


def regenerate_missing_tiles():
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)
    with connection:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(GET_TILING_DONE)

        if verbose and cur.rowcount > 0:
            print 'Regenerating missing tiles for', cur.rowcount, 'media files...'
            sys.stdout.flush()

        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            centre_id = record['cid']
            pipeline_id = record['lid']
            genotype_id = record['gid']
            strain_id = record['sid']
            procedure_id = record['pid']
            parameter_id = record['qid']
            file_extension = record['extension']
            file_checksum = record['checksum']

            tiles_path = get_tile_storage_path(file_checksum)
            if not (tiles_path and os.path.exists(tiles_path) and os.path.isfile(tiles_path + 'thumbnail.jpg')):
                original_media = get_original_media_path(centre_id, pipeline_id, genotype_id, strain_id,
                                                         procedure_id, parameter_id, media_id, file_extension)
                generate_image_tiles(connection, media_id, original_media, file_checksum)


def print_usage():
    print '\nPhenoDCC media downloader and tile generator\n(http://www.mousephenotype.org)'
    print 'Version', VERSION, '\n'
    print 'USAGE: phenodcc_media.py [-p | --prepare | -d | --download | -t | --tile | -v | --verbose | -h | --help]\n'
    print '    -p, --prepare    Prepare media files by marking them for download.'
    print '    -d, --download   Download media files that was marked for download.'
    print '    -t, --tile       Generate tiles for all of the image media files'
    print '                     that was downloaded successfully.'
    print '    -r, --regen      Identify missing tiles and re-generate them from original media files.'
    print '    -v, --verbose    Verbose output of execution status.'
    print '    -h, --help       Displays this help information.\n'
    print 'The configuration file for running this script is set in \'phenodcc_media.config\'.'
    print 'The following settings are allowed:\n'
    print '    tracker - Database for getting active contexts and media file URLs.'
    print '      media - Database where we track the download and processing of media files.'
    print '       tile - Set tile size.'
    print '     scales - Set zooming scales.\n'
    print 'Single Instance\n---------------'
    print 'To allow the script to be invoked periodically as part of an automated system,'
    print 'the script uses file locking to allow only one running instance of a phase.'
    print 'Hence, a file name prepare.lock, download.lock or tiling.lock is created in the'
    print 'directory from which the script is invoked. Note that this only works if the script'
    print 'is always run from the same directory. Two different phases can run simultaneously.'
    sys.stdout.flush()


def parse_commandline():
    global verbose
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdprtv", ["help", "download", "prepare", "regen", "tile", "verbose"])
    except getopt.GetoptError as error:
        print error
        print_usage()
        sys.exit()

    if not opts:
        print_usage()
        sys.exit()

    what_to_do = None
    for option, argument in opts:
        if option in ("-p", "--prepare"):
            what_to_do = "prepare"
        elif option in ("-d", "--download"):
            what_to_do = "download"
        elif option in ("-t", "--tile"):
            what_to_do = "tile"
        elif option in ("-r", "--regen"):
            what_to_do = "regen"
        elif option in ("-v", "--verbose"):
            verbose = True
        elif option in ("-h", "--help"):
            pass
    return what_to_do


def main():
    what_to_do = parse_commandline()
    if what_to_do:
        get_configuration()
        set_phase_status_ids()

        if what_to_do == 'prepare':
            fp = open('prepare.lock', 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                start_time = datetime.now()
                print 'Started preparing for download at:', start_time
                add_files_to_download()
                fp.close()
                end_time = datetime.now()
                print 'Preparation for download ended at:', end_time
                print 'Elapsed time:', end_time - start_time
            except IOError as e:
                print 'Already preparing media files for download... check prepare.lock'
                sys.stdout.flush()
                if verbose:
                    print "main -", e
                    sys.stdout.flush()
                sys.exit()
        elif what_to_do == 'download':
            fp = open('download.lock', 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # The fix for interrupted phases should only be invoked before download begins.
                # The add files process above only inserts new media files to be downloaded;
                # hence, we should not fix there. Since checksum and tiling follows download,
                # the fix will cascade automatically.
                start_time = datetime.now()
                print 'Started fixing interrupted downloads at:', start_time
                fix_interrupted_phases()
                end_time = datetime.now()
                print 'Finished fixing interrupted downloads at:', end_time
                print 'Elapsed time:', end_time - start_time

                start_time = datetime.now()
                print 'Started downloading media files at:', start_time
                download_media()
                fp.close()
                end_time = datetime.now()
                print 'Finished downloading media files at:', end_time
                print 'Elapsed time:', end_time - start_time
            except IOError as e:
                print 'Already downloading media files... check download.lock'
                sys.stdout.flush()
                if verbose:
                    print "main -", e
                    sys.stdout.flush()
                sys.exit()
        elif what_to_do == 'tile':
            fp = open('tiling.lock', 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                start_time = datetime.now()
                print 'Started tiling images at:', start_time
                generate_tiles()
                fp.close()
                end_time = datetime.now()
                print 'Finished tiling images at:', end_time
                print 'Elapsed time:', end_time - start_time
            except IOError as e:
                print 'Already tiling image files... check tiling.lock'
                sys.stdout.flush()
                if verbose:
                    print "main -", e
                    sys.stdout.flush()
                sys.exit()
        elif what_to_do == 'regen':
            fp = open('tiling.lock', 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                regenerate_missing_tiles()
                fp.close()
            except IOError as e:
                print 'Already tiling image files... check tiling.lock'
                sys.stdout.flush()
                if verbose:
                    print "main -", e
                    sys.stdout.flush()
                sys.exit()
    else:
        print_usage()
        sys.exit()


if __name__ == "__main__":
    main()
