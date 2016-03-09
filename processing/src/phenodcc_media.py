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
from urlparse import urlparse
import paramiko
import hashlib
import sys
from subprocess import call
from PIL import Image
import fcntl
import time
from datetime import datetime

VERSION = '0.8.9'

# Settings
MAX_DOWNLOAD_RETRIES = 1
SLEEP_SECS_BEFORE_RETRY = 20  # 20 seconds

# Global variables
sleep_message = None
HASH_BLOCK_SIZE = 65536
opt_verbose = True
opt_specified_centre = None
download_centre_id = None
opt_config_file = None
opt_lock_dir = None
what_to_do = None
connection = None
MEDIA_HOSTNAME = MEDIA_USERNAME = MEDIA_PASSWORD = MEDIA_DATABASE = \
    ORIGINAL_MEDIA_FILES_DIR = IMAGE_TILES_DIR = TILE_SIZE = IMAGE_SCALES = None


# MySQL statements
DB_LOG_ERROR = '''
insert into phenodcc_media.error_logs
(media_id, phase_id, error_msg, created)
values (%s, %s, %s, now())
'''

DB_CENTRE_WITH_SHORTNAME = '''
select centre_id
from phenodcc_overviews.centre
where short_name = %s
limit 1
'''

DB_GET_MEDIA_FILES = '''
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

DB_ADD_FILE_TO_DOWNLOAD = '''
insert into phenodcc_media.media_file
(cid, lid, gid, sid, pid, qid, mid, url, extension_id, is_image, phase_id, status_id, created)
values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
'''

# Note that many resubmissions might be happening, which should all point to
# the latest successful download. This is why we order them in descending order by
# the id (because lower ids are the oldest entries) and limit result by one.
# We are only interested in the state of the last successful download
# (i.e., phase > download)
DB_CHECK_IF_URL_ALREADY_DOWNLOADED = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension
from phenodcc_media.media_file as f
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where
    f.phase_id > 1
    and f.status_id = 3
    and f.url = %s
order by id desc
limit 1
'''

DB_CHECK_IF_FILE_ALREADY_EXISTS = '''
select id from phenodcc_media.media_file
where
    cid = %s
    and lid = %s
    and gid = %s
    and sid = %s
    and pid = %s
    and qid = %s
    and mid = %s
'''

DB_CHECK_IF_EXTENSION_EXISTS = '''
select id
from phenodcc_media.file_extension
where extension = %s
'''

DB_ADD_FILE_EXTENSION = '''
insert into phenodcc_media.file_extension (extension) values (%s)
'''

DB_GET_SERVER_CREDENTIAL = '''
select protocol_id, hostname, username, accesskey, base_path
from phenodcc_tracker.file_source
where centre_id = %s
'''

DB_GET_FILES_TO_BE_DOWNLOADED = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, f.url, e.extension
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where
    f.cid = %s
    and p.short_name = "download"
    and s.short_name = "pending"
order by f.id
'''

DB_GET_IMAGE_FILES_TO_TILE = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where
    f.is_image = 1
    and f.checksum is not null
    and p.short_name = "checksum"
    and s.short_name = "done"
order by f.id
'''

DB_GET_INTERRUPTED_DOWNLOADS = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where
    f.cid = %s
    and p.short_name = "download"
    and s.short_name = "running"
'''

DB_GET_INTERRUPTED_CHECKSUM = '''
select f.id
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
where
    f.cid = %s and
    (
        p.short_name = "checksum"
        and s.short_name = "running"
    )
    or (
        p.short_name = "download"
        and s.short_name = "done"
    )
'''

DB_GET_INTERRUPTED_TILING = '''
select f.id, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
where p.short_name = "tile" and s.short_name = "running"
'''

DB_GET_TILING_DONE = '''
select f.id, f.cid, f.lid, f.gid, f.sid, f.pid, f.qid, e.extension, f.checksum
from
    phenodcc_media.media_file f
    left join phenodcc_media.phase p on (f.phase_id = p.id)
    left join phenodcc_media.a_status s on (f.status_id = s.id)
    left join phenodcc_media.file_extension e on (f.extension_id = e.id)
where
    p.short_name = "tile"
    and s.short_name = "done"
order by f.id
'''

DB_GET_PHASE_ID = '''
select id from phenodcc_media.phase where short_name = %s limit 1
'''

DB_GET_STATUS_ID = '''
select id from phenodcc_media.a_status where short_name = %s limit 1
'''

DB_UPDATE_PHASE_STATUS = '''
update phenodcc_media.media_file set phase_id = %s, status_id = %s where id = %s
'''

DB_UPDATE_CHECKSUM = '''
update phenodcc_media.media_file set checksum = %s where id = %s
'''

DB_UPDATE_IMAGE_SIZE = '''
update phenodcc_media.media_file set width = %s, height = %s where id = %s
'''

DOWNLOAD_PHASE = -1
CHECKSUM_PHASE = -1
TILE_GENERATION_PHASE = -1
PENDING_STATUS = -1
RUNNING_STATUS = -1
DONE_STATUS = -1
FAILED_STATUS = -1


def info(msg):
    if opt_verbose:
        print msg
        sys.stdout.flush()


def info_nonewline(msg):
    if opt_verbose:
        print msg,
        sys.stdout.flush()


def error(msg):
    print '[ERROR]: ' + msg
    sys.stdout.flush()


def cleanup_and_exit(exit_status):
    if connection and connection.open:
        info('Closing database connection...')
        connection.close()
    else:
        info('No active database connection...')
    info('Exiting application...Bye')
    sys.exit(exit_status)


def error_exit(msg):
    print msg
    cleanup_and_exit(1)


def connect_to_database():
    global connection
    connection = MySQLdb.connect(MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD, MEDIA_DATABASE)


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


def log_error(media_id, phase_id, error_msg):
    cur = connection.cursor()
    cur.execute(DB_LOG_ERROR, (media_id, phase_id, error_msg))
    connection.commit()


def set_phase_status_ids():
    global DOWNLOAD_PHASE, CHECKSUM_PHASE, TILE_GENERATION_PHASE, \
        PENDING_STATUS, RUNNING_STATUS, DONE_STATUS, FAILED_STATUS
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_GET_PHASE_ID, ("download",))
    DOWNLOAD_PHASE = cur.fetchone()['id']
    cur.execute(DB_GET_PHASE_ID, ("checksum",))
    CHECKSUM_PHASE = cur.fetchone()['id']
    cur.execute(DB_GET_PHASE_ID, ("tile",))
    TILE_GENERATION_PHASE = cur.fetchone()['id']
    cur.execute(DB_GET_STATUS_ID, ("pending",))
    PENDING_STATUS = cur.fetchone()['id']
    cur.execute(DB_GET_STATUS_ID, ("running",))
    RUNNING_STATUS = cur.fetchone()['id']
    cur.execute(DB_GET_STATUS_ID, ("done",))
    DONE_STATUS = cur.fetchone()['id']
    cur.execute(DB_GET_STATUS_ID, ("failed",))
    FAILED_STATUS = cur.fetchone()['id']


# Returns a tuple that determines the file type
# 1) The file extension, and
# 2) A boolean value that is true if the file is an image; false, otherwise.
def get_file_type(url):
    extension_id = None
    is_image = 0
    matches = re.search(r'.*\.(\w+)$', url)
    if matches:
        extension = matches.group(1).lower()
        if re.match(r'^(bmp|dcm|jpeg|jpg|png|tif|tiff)$', extension):
            is_image = 1
        cur = connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(DB_CHECK_IF_EXTENSION_EXISTS, (extension,))
        if cur.rowcount:
            extension_id = cur.fetchone()['id']
        else:
            cur.execute(DB_ADD_FILE_EXTENSION, (extension,))
            connection.commit()
            extension_id = connection.insert_id()
    else:
        info('Invalid media file name in "' + url + '" ...')
    return extension_id, is_image


# Adds a URL into the list of files to be downloaded and processed
# Note that the actual downloading and processing of the files are
# handled by a different process. This prevents the download and
# processing of files from blocking the crawler.
def add_files_to_download():
    ignore_mousephenotype_org = re.compile(r"^http[s]?://(?:www.)?mousephenotype.org/.*$")
    tracker_cur = connection.cursor(MySQLdb.cursors.DictCursor)
    tracker_cur.execute(DB_GET_MEDIA_FILES)
    if tracker_cur.rowcount > 0:
        info(str(tracker_cur.rowcount) + ' media files found...')
        to_download = 0
        already_downloaded = 0
        media_cur = connection.cursor(MySQLdb.cursors.DictCursor)
        already_cur = connection.cursor(MySQLdb.cursors.DictCursor)
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

            if ignore_mousephenotype_org.match(url_to_download):
                info('Ignoring URL: ' + url_to_download + '; file hosted at mousephenotype.org')
                continue

            # We ignore files that have already been processed, or is
            # mark for processing. We do this to avoid race condition.
            # This script is run by the crawler, and the download and
            # processing is run by a different process. Since download
            # and processing only works on files that are already marked,
            # restricting this script to additions prevents a race.
            already_cur.execute(DB_CHECK_IF_FILE_ALREADY_EXISTS, (
                centre_id, pipeline_id, genotype_id, strain_id,
                procedure_id, parameter_id, measurement_id
            ))
            temp = '    Url "' + url_to_download
            if already_cur.rowcount == 0:
                extension_id, is_image = get_file_type(url_to_download)
                if extension_id is None:
                    info(temp + '" has invalid filename extension...')
                else:
                    media_cur.execute(DB_ADD_FILE_TO_DOWNLOAD, (
                        centre_id, pipeline_id, genotype_id, strain_id,
                        procedure_id, parameter_id, measurement_id,
                        url_to_download, extension_id, is_image,
                        DOWNLOAD_PHASE, PENDING_STATUS
                    ))
                    connection.commit()
                    to_download += 1
                    info(temp + '" has been added for download and processing...')
            else:
                already_downloaded += 1
        info(str(already_downloaded) + ' media files already downloaded...')
        info(str(to_download) + ' new media files added to download queue...')
    else:
        info('No new media files added. None recorded for download...')


def get_credential(centre_id):
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_GET_SERVER_CREDENTIAL, (centre_id,))
    credential = None
    if cur.rowcount:
        credential = cur.fetchone()
        if credential['accesskey'] == '':
            credential['accesskey'] = None
    return credential


def download_file(url, save_as, max_attempts):
    num_retries = 1
    while num_retries <= max_attempts:
        info_nonewline('Attempt ' + str(num_retries))
        r = None
        success = False
        try:
            r = urllib2.urlopen(url)
            with open(save_as, 'wb') as f:
                shutil.copyfileobj(r, f)
            success = True
            info('[ SUCCESS ]')
        except (urllib2.URLError, IOError) as e:
            info('[ FAIL ]')
            error(str(e))
            num_retries += 1
            if num_retries > max_attempts:
                info('Giving up the download, maximum retries reached')
                raise e
            else:
                info(sleep_message)
                time.sleep(SLEEP_SECS_BEFORE_RETRY)
        finally:
            if r:
                r.close()
        if success:
            return


def get_ftp_file(url, save_as, cred):
    try:
        loc = "ftp://"
        # temporary hack to proceed with anonymous download if processing Jax
        if opt_specified_centre != 'J' \
                and cred["username"] is not None \
                and cred["accesskey"] is not None:
            loc = loc + cred["username"] + ":" + cred["accesskey"] + "@"
        loc = loc + url.netloc + url.path
        download_file(loc, save_as, MAX_DOWNLOAD_RETRIES)
    except (urllib2.URLError, IOError) as e:
        if opt_specified_centre == 'Tcp': # To prevent incorrect login ban
            raise e
            return
        error('Download with username/password failed')
        error(str(e))
        info('Will attempt anonymous download')
        try:
            loc = "ftp://" + url.netloc + url.path
            download_file(loc, save_as, 1)
        except (urllib2.URLError, IOError):
            raise e  # We wish to record the first exception (as that is the expected one)


def get_sftp_file(url, save_as, cred):
    num_retries = 1
    while num_retries <= MAX_DOWNLOAD_RETRIES:
        info_nonewline('Attempt ' + str(num_retries))
        success = False
        sftp = None
        transport = None
        try:
            pkey = paramiko.RSAKey.from_private_key_file('/home/dcccrawler/.ssh/id_rsa')
            transport = paramiko.Transport((url.netloc.split(':')[0], 22))
            transport.connect(username=cred["username"], password=cred["accesskey"], pkey=pkey)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(url.path, save_as)
            success = True
            info('[ SUCCESS ]')
        except (IOError, paramiko.PasswordRequiredException, paramiko.SSHException) as e:
            info('[ FAIL ]')
            error(str(e))
            num_retries += 1
            if num_retries > MAX_DOWNLOAD_RETRIES:
                error('Giving up the download, maximum retries reached')
                raise e
            else:
                info(sleep_message)
                time.sleep(SLEEP_SECS_BEFORE_RETRY)
        finally:
            if sftp:
                sftp.close()
            if transport and transport.isAlive():
                transport.close()
        if success:
            return


def get_file(url_to_download, save_as, cred):
    # make the supplied url safe for download
    url = urlparse(urllib2.quote(url_to_download, safe="%/:=&?~#+!$,;'@()*[]"))
    info('Downloading "' + url_to_download + '" and saving as file "' + save_as + '"')
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
        error(str(e))
        return None
    return has_generator.hexdigest()


# Set the checksum of the media file record by calculating the SHA1 checksum of the downloaded file.
def set_checksum(media_id, file_saved_as):
    modify = connection.cursor()
    modify.execute(DB_UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, RUNNING_STATUS, media_id))
    connection.commit()
    sha1 = get_sha1(file_saved_as)
    if sha1 is None:
        modify.execute(DB_UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, FAILED_STATUS, media_id))
    else:
        modify.execute(DB_UPDATE_CHECKSUM, (sha1, media_id))
        modify.execute(DB_UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, DONE_STATUS, media_id))
    connection.commit()
    return sha1


# First check if the URL was already downloaded successfully. This happens when 
# centres resubmit the same URLs, and because new measurement ids are assigned,
# the same URL is marked as a new media file. Since downloading files is
# really expensive in terms of bandwidth and storage space, we try to optimise this
# by instead creating a symbolic link to the existing file.
def check_and_download(url_to_download, file_save_as, credentials):
    download_file_as_new = False
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_CHECK_IF_URL_ALREADY_DOWNLOADED, (url_to_download,))
    if cur.rowcount == 0:
        download_file_as_new = True
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
            if os.path.exists(existing_file):
                info('URL "' + url_to_download + '" already downloaded\n' +
                     'Creating symbolic link "'
                     + file_save_as + '" -> "' + existing_file + '"')
                src_split = os.path.split(file_save_as)
                os.symlink(os.path.relpath(existing_file, src_split[0]), file_save_as)
            else:
                error('Downloaded file "' + existing_file + '" for the URL "'
                      + url_to_download
                      + '" no longer exists. Won\'t create symbolic link')
                download_file_as_new = True
        except OSError:
            # If we cannot create a symlink, probably the file is no longer
            # there. So, just re-download it again.
            error('Failed to create symbolic link from "' + file_save_as
                  + '" to "' + existing_file + '"')
            download_file_as_new = True
    if download_file_as_new:
        get_file(url_to_download, file_save_as, credentials)


# Download file that has not been downloaded and update download status.
# connection - Connection to use for accessing the database
# media_id - Primary key of the record associated with the file
# credentials - Credentials for accessing the file server
# url_to_download - URL to download
# file_save_as - Where to save the file once downloaded
def retrieve_file(media_id, credentials, url_to_download, file_save_as):
    download_successful = False
    if os.path.exists(file_save_as):
        info('File "' + file_save_as + '" already exists... will skip')
        download_successful = True
    else:
        cur = connection.cursor()
        try:
            cur.execute(DB_UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, RUNNING_STATUS, media_id))
            connection.commit()
            check_and_download(url_to_download, file_save_as, credentials)
            cur.execute(DB_UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, PENDING_STATUS, media_id))
            connection.commit()
            download_successful = True
        except (MySQLdb.Error, OSError, IOError, urllib2.URLError,
                paramiko.PasswordRequiredException, paramiko.SSHException) as e:
            cur.execute(DB_UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, FAILED_STATUS, media_id))
            connection.commit()
            log_error(media_id, DOWNLOAD_PHASE, str(e))
    return download_successful


def download_media():
    centre = -1
    credentials = None
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_GET_FILES_TO_BE_DOWNLOADED, (download_centre_id,))
    if cur.rowcount > 0:
        info('Downloading ' + str(cur.rowcount) + ' media files...')
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

            info('---------------------------------')
            info('Processing media id: ' + str(media_id))
            info('---------------------------------')

            # this assumes that all of the media files for a centre are processed in groups.
            # See the ordering in GET_FILES_TO_BE_DOWNLOADED.
            if centre != centre_id:
                centre = centre_id
                credentials = get_credential(centre)

            # Get path for systematically storing the original media file that will be downloaded.
            create_media_storage_path(centre_id, pipeline_id, genotype_id,
                                      strain_id, procedure_id, parameter_id)
            file_save_as = get_original_media_path(centre_id, pipeline_id,
                                                   genotype_id, strain_id,
                                                   procedure_id, parameter_id,
                                                   media_id, file_extension)
            download_successful = retrieve_file(media_id, credentials,
                                                url_to_download, file_save_as)
            if download_successful:
                set_checksum(media_id, file_save_as)
    else:
        info('No media files to download...')


# Determine width and height of an image file
def get_image_size(image_file):
    size = None
    if os.path.isfile(image_file):
        try:
            img = Image.open(image_file)
            size = img.size
        except (IOError, EOFError) as e:
            error('Failed to open file "' + image_file + '"...')
            error(str(e))
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
            error('Tiles directory ' + original_scale_tiles_path + ' does not exist...')
            error(str(e))
    return size


# Update meta-data for the image tiles that have been generated from the original media.
def update_tile_metadata(media_id, image_size):
    cur = connection.cursor()
    if image_size is None:
        cur.execute(DB_UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, FAILED_STATUS, media_id))
    else:
        cur.execute(DB_UPDATE_IMAGE_SIZE, image_size + (media_id,))
        cur.execute(DB_UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, DONE_STATUS, media_id))
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
def generate_image_tiles(media_id, original_media, file_checksum):
    cur = connection.cursor()
    cur.execute(DB_UPDATE_PHASE_STATUS, (TILE_GENERATION_PHASE, RUNNING_STATUS, media_id))
    connection.commit()

    # To work around file system restrictions on the number of items allowed in a
    # directory, we do not store the tiles using the file_checksum. Instead, we decompose
    # the 40 character file_checksum into a path that is 10 levels deep, where the directory
    # name contains four characters.
    tiles_path = get_tile_storage_path(file_checksum)

    # Run the script that generates the image tiles.
    return_code = call(['./generate_tiles_for_image.sh', original_media,
                        IMAGE_TILES_DIR, TILE_SIZE, IMAGE_SCALES])
    if return_code == 0:
        update_tile_metadata(media_id, get_image_width_height(tiles_path, TILE_SIZE))
    else:
        update_tile_metadata(media_id, None)
    return return_code


# Generate tiles for all of the image media files.
def generate_tiles():
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_GET_IMAGE_FILES_TO_TILE)
    if cur.rowcount > 0:
        info('Generating tiles for ' + str(cur.rowcount) + ' media files...')
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

            info('---------------------------------')
            info('Processing media id: ' + str(media_id))
            info('---------------------------------')

            original_media = get_original_media_path(centre_id, pipeline_id,
                                                     genotype_id, strain_id,
                                                     procedure_id, parameter_id,
                                                     media_id, file_extension)
            generate_image_tiles(media_id, original_media, file_checksum)
    else:
        info('No image files to tile...')


def fix_interrupted_downloads():
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    modify_cur = connection.cursor()
    cur.execute(DB_GET_INTERRUPTED_DOWNLOADS, (download_centre_id,))
    if cur.rowcount > 0:
        info('Fixing ' + str(cur.rowcount) + ' interrupted downloads...')
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
            info('Will re-download media file with id ' + str(media_id))

            # If the download was interrupted, any existing file could be corrupted or incomplete.
            # Since the normal downloader skips existing files, we must first delete any existing
            # file so that the media file is downloaded again.
            original_media = get_original_media_path(centre_id, pipeline_id,
                                                     genotype_id, strain_id,
                                                     procedure_id, parameter_id,
                                                     media_id, file_extension)
            if original_media and os.path.exists(original_media):
                if os.path.islink(original_media):
                    info('Removing existing symbolic link "' + original_media + '"')
                    os.remove(original_media)
                else:
                    new_name = original_media + datetime.now().strftime("_%Y_%m_%d_%H_%M") + '.old'
                    info('Renaming existing file "' + original_media + '" to "' + new_name + '"')
                    os.rename(original_media, new_name)

            # Now, mark this for re-downloading in the next download run.
            modify_cur.execute(DB_UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, PENDING_STATUS, media_id))
            connection.commit()
    else:
        info('No interrupted downloads found...')


def fix_interrupted_checksum():
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    modify_cur = connection.cursor()
    cur.execute(DB_GET_INTERRUPTED_CHECKSUM, (download_centre_id,))
    if cur.rowcount > 0:
        info('Fixing ' + str(cur.rowcount) + ' interrupted checksum calculations...')
        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            info('Will re-calculate checksum for media file with id ' + str(media_id))
            # Mark this for re-downloading in the next download run.
            # Since only checksum was interrupted, the download must have completed
            # successfully. By not deleting this file, the download phase will be skipped
            # followed by calculation of the checksum as usual.
            modify_cur.execute(DB_UPDATE_PHASE_STATUS, (DOWNLOAD_PHASE, PENDING_STATUS, media_id))
            connection.commit()
    else:
        info('No interrupted checksum calculations to fix...')


def fix_interrupted_tiling():
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    modify = connection.cursor()
    cur.execute(DB_GET_INTERRUPTED_TILING)
    if cur.rowcount > 0:
        info('Fixing ' + str(cur.rowcount) + ' interrupted media tiling...')
        for i in range(cur.rowcount):
            record = cur.fetchone()
            media_id = record['id']
            file_checksum = record['checksum']
            info('    Will re-generate tiles for media file with id ' +
                 str(media_id) + ' and checksum ' + file_checksum)
            # If the tiling was interrupted, it is highly likely that the tiles set is
            # incomplete. We therefore need to assume that the worst has happen and
            # re-generate the tiles set all over again. To do this, we must first delete
            # the existing tiles directory.
            tiles_path = get_tile_storage_path(file_checksum)
            if tiles_path and os.path.exists(tiles_path):
                shutil.rmtree(tiles_path)

            # Now, mark this for tile re-generation.
            modify.execute(DB_UPDATE_PHASE_STATUS, (CHECKSUM_PHASE, DONE_STATUS, media_id))
            connection.commit()
    else:
        info('No interrupted tiling to fix...')


def regenerate_missing_tiles():
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_GET_TILING_DONE)
    if cur.rowcount > 0:
        info('Regenerating missing tiles for ' + str(cur.rowcount) + ' media files...')
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
            if not (tiles_path and os.path.exists(tiles_path)
                    and os.path.isfile(tiles_path + 'thumbnail.jpg')):
                original_media = get_original_media_path(centre_id, pipeline_id,
                                                         genotype_id, strain_id,
                                                         procedure_id, parameter_id,
                                                         media_id, file_extension)
                generate_image_tiles(media_id, original_media, file_checksum)
    else:
        info('No missing tiles to regenerate...')


def print_usage():
    print '\nPhenoDCC media downloader and tile generator\n(http://www.mousephenotype.org)'
    print 'Version', VERSION, '\n'
    print 'USAGE:\n\tphenodcc_media.py [-p | --prepare | -d | --download | -t | --tile |'
    print '\t\t -c | --centre | -x | --config-file | -l | --lock-dir |'
    print '\t\t -silent | --silent | -h | --help]\n'
    print '    -p, --prepare      Prepare media files by marking them for download.'
    print '    -d, --download     Download media files that was marked for download.'
    print '    -t, --tile         Generate tiles for all of the image media files'
    print '                       that was downloaded successfully.'
    print '    -r, --regen        Identify missing tiles and re-generate them from original image.'
    print '    -c, --centre       Restrict download to given centre.'
    print '    -l, --lock-dir     Directory where single instance locks are held.'
    print '    -x, --config-file  Which file to use for getting configuration.'
    print '    -s, --silent       By default, the application will produce verbose output'
    print '                       of the execution status. Silent will disable this.'
    print '                       Error messages will continue to be produced in silent mode.'
    print '    -h, --help         Displays this help information.\n'
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


def print_usage_and_exit():
    print_usage()
    sys.exit(1)


def is_valid_centre(centre):
    global connection, download_centre_id
    if centre is None:
        error('Please supply a centre to associate with this download')
        print_usage()
        return False
    cur = connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(DB_CENTRE_WITH_SHORTNAME, (centre,))
    if cur.rowcount == 0:
        error('Supplied centre "' + centre + '" is invalid...')
        return False
    else:
        download_centre_id = cur.fetchone()['centre_id']
    return True


def prepare_lock_name(action):
    lock_name = opt_lock_dir + action + '_'
    if opt_specified_centre:
        lock_name = lock_name + opt_specified_centre
    return lock_name + '.lock'


def log_timed(message, when):
    if opt_verbose:
        print message, when
        sys.stdout.flush()


def prepare_for_download():
    lock_name = opt_lock_dir + 'prepare.lock'
    fp = None
    try:
        fp = open(lock_name, 'w')
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started preparing for download at:', start_time)
        add_files_to_download()
        end_time = datetime.now()
        log_timed('Preparation for download ended at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        info('---------------------------------')
    except IOError as e:
        error('Already preparing media files for download... check "' + lock_name + '"')
        error(str(e))
    finally:
        if fp and not fp.closed:
            fp.close()
        os.remove(lock_name)


# Fixing interrupted downloads must happen inside the download phase because
# putting it anywhere else might conflict with current downloads that are active.
# To prevent download phase conflicts, a downloader instance should only fix
# downloads that belong to its associated centre.
def download_the_media():
    if not is_valid_centre(opt_specified_centre):
        cleanup_and_exit(1)
    lock_name = prepare_lock_name('download')
    fp = None
    try:
        fp = open(lock_name, 'w')
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started fixing interrupted downloads at:', start_time)
        fix_interrupted_downloads()
        fix_interrupted_checksum()
        end_time = datetime.now()
        log_timed('Finished fixing interrupted downloads at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started downloading media files at:', start_time)
        download_media()
        end_time = datetime.now()
        log_timed('Finished downloading media files at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        info('---------------------------------')
    except IOError as e:
        error('Already downloading media files... check "' + lock_name + '"')
        error(str(e))
    finally:
        if fp and not fp.closed:
            fp.close()
        os.remove(lock_name)


def tile_image_media():
    lock_name = opt_lock_dir + 'tiling.lock'
    fp = None
    try:
        fp = open(lock_name, 'w')
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started fixing interrupted tiling at:', start_time)
        fix_interrupted_tiling()
        end_time = datetime.now()
        log_timed('Finished fixing interrupted tiling at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started tiling images at:', start_time)
        generate_tiles()
        end_time = datetime.now()
        log_timed('Finished tiling images at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        info('---------------------------------')
    except IOError as e:
        error('Already tiling image files... check "' + lock_name + '"')
        error(str(e))
    finally:
        if fp and not fp.closed:
            fp.close()
        os.remove(lock_name)


def regenerate_tiles():
    lock_name = opt_lock_dir + 'tiling.lock'
    fp = None
    try:
        fp = open(lock_name, 'w')
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        start_time = datetime.now()
        info('---------------------------------')
        log_timed('Started regenerating missing tiles at:', start_time)
        regenerate_missing_tiles()
        end_time = datetime.now()
        log_timed('Finished regenerating  missing tiles at:', end_time)
        log_timed('Elapsed time:', end_time - start_time)
        info('---------------------------------')
    except IOError as e:
        error('Already tiling image files... check "' + lock_name + '"')
        error(str(e))
    finally:
        if fp and not fp.closed:
            fp.close()
        os.remove(lock_name)


def check_config_file():
    global opt_config_file
    if opt_config_file:
        if not os.path.isfile(opt_config_file):
            error_exit('Supplied config file "' + opt_config_file
                       + '" does not exists...')
    else:
        error('Please specify a media downloader config file...')
        print_usage_and_exit()


def check_dir_validity(directory, msg):
    if not os.path.isdir(directory):
        error_exit(msg + 'does not exists...')
    if not os.access(directory, os.W_OK):
        error_exit(msg + 'is not writable...')


def check_media_directory(directory):
    if not directory.endswith('/'):
        directory += '/'
    msg = 'Directory "' + directory + \
          '" specified in config file "' + opt_config_file + '" '
    check_dir_validity(directory, msg)
    return directory


def check_lock_directory(directory):
    if not directory.endswith('/'):
        directory += '/'
    check_dir_validity(directory, 'Lock directory "' + directory + '" ')
    return directory


def get_configuration():
    global opt_config_file, sleep_message
    global MEDIA_DATABASE, MEDIA_HOSTNAME, MEDIA_USERNAME, MEDIA_PASSWORD
    global ORIGINAL_MEDIA_FILES_DIR, IMAGE_TILES_DIR
    global TILE_SIZE, IMAGE_SCALES

    check_config_file()
    config = ConfigParser.RawConfigParser()
    config_open = config.read(opt_config_file)
    if len(config_open) == 0:
        error_exit('Failed to read config file "' + opt_config_file + '"...')

    MEDIA_DATABASE = config.get('media', 'database')
    MEDIA_HOSTNAME = config.get('media', 'hostname')
    MEDIA_USERNAME = config.get('media', 'username')
    MEDIA_PASSWORD = config.get('media', 'password')

    # Directory where media files should be downloaded
    # and where the generated images tiles should go
    ORIGINAL_MEDIA_FILES_DIR = check_media_directory(config.get('dirs', 'originals_dir'))
    IMAGE_TILES_DIR = check_media_directory(config.get('dirs', 'tiles_dir'))

    # Concerning tile generation
    TILE_SIZE = config.get('tiling', 'tile_size')
    IMAGE_SCALES = config.get('tiling', 'image_scales')

    if SLEEP_SECS_BEFORE_RETRY > 60:
        sleep_message = str(SLEEP_SECS_BEFORE_RETRY / 60) + ' minutes'
    else:
        sleep_message = str(SLEEP_SECS_BEFORE_RETRY) + ' seconds'
    sleep_message = 'Sleeping for ' + sleep_message + ' before re-attempt'


def parse_options(opts):
    global what_to_do, opt_verbose, opt_specified_centre, opt_config_file, opt_lock_dir
    for option, argument in opts:
        if option in ("-p", "--prepare"):
            what_to_do = "prepare"
        elif option in ("-d", "--download"):
            what_to_do = "download"
        elif option in ("-t", "--tile"):
            what_to_do = "tile"
        elif option in ("-r", "--regen"):
            what_to_do = "regen"
        elif option in ("-c", "--centre"):
            opt_specified_centre = argument
        elif option in ("-l", "--lock-dir"):
            opt_lock_dir = argument
        elif option in ("-x", "--config-file"):
            opt_config_file = argument
        elif option in ("-s", "--silent"):
            opt_verbose = False
        elif option in ("-h", "--help"):
            print_usage_and_exit()


def parse_commandline():
    global opt_lock_dir
    options = ["help", "download", "prepare", "regen", "centre=",
               "lock-dir=", "config-file=", "tile", "silent"]
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdprc:x:l:ts", options)
        if opts:
            parse_options(opts)
            if opt_lock_dir:
                opt_lock_dir = check_lock_directory(opt_lock_dir)
            else:
                error('Please specify a lock directory...')
                print_usage_and_exit()
    except getopt.GetoptError as e:
        error(e)


def main():
    global what_to_do
    parse_commandline()
    if what_to_do:
        get_configuration()
        connect_to_database()
        set_phase_status_ids()
        if what_to_do == 'prepare':
            prepare_for_download()
        elif what_to_do == 'download':
            download_the_media()
        elif what_to_do == 'tile':
            tile_image_media()
        elif what_to_do == 'regen':
            regenerate_tiles()
        cleanup_and_exit(1)
    else:
        error('Please supply a command for the media downloader to execute...')
        print_usage_and_exit()
    return 0


if __name__ == "__main__":
    main()
