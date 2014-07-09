/******************************************************************************
 *                      The PhenoDCC Media Database                           *
 *                                                                            *
 * DESCRIPTION:                                                               *
 * This is the database that the PhenoDCC uses for tracking download,         *
 * processing and dissemination of media files.                               *
 *                                                                            *
 * Copyright (c) 2014, Medical Research Council Harwell                       *
 * Written by: G. Yaikhom (g.yaikhom@har.mrc.ac.uk)                           *
 *                                                                            *
 *****************************************************************************/

/*

drop database if exists phenodcc_media;
create database phenodcc_media;
grant all on phenodcc_media.* to 'dccadmin'@'localhost';
flush privileges;

*/

use phenodcc_media;

/* A media file URL can be in one of the following phases of download and processing. */
drop table if exists phase;
create table phase (
       id smallint unsigned not null auto_increment, /* this will be used as the processing phase code */
       short_name varchar(64) not null, /* the short name of the processing phase */
       description text, /* a brief description of what happens in this processing phase */
       last_update timestamp not null default current_timestamp on update current_timestamp,
       index (short_name),
       primary key (id),
       unique (short_name)
) engine = innodb;

/* Order is important */
insert into phase (short_name, description) values
       ('download', 'Download media file from the file data source'),
       ('checksum', 'Calculate checksum'),
       ('tile', 'Large images are broken down to smaller tiles')
       ;

/* Every processing phase is associated with it a status, which is either 'pending', 'running', 'done' (successful completion), 'cancelled', or 'failed' (termination due to processing errors). Again, the temporal ordering of the status must be maintained. In other words, the status for a phase cannot change arbitrarily; they must follow: pending, running, done, cancelled, or failed. Note that the PhenoDCC system relies on the failure status having the highest priority. */
drop table if exists a_status;
create table a_status (
       id smallint unsigned not null auto_increment, /* this will be used as the progress status code */
       short_name varchar(64) not null, /* the short name we will use for the status */
       description text, /* a brief description of the status */
       last_update timestamp not null default current_timestamp on update current_timestamp,
       index (short_name),
       primary key (id),
       unique (short_name)
) engine = innodb;

insert into a_status (short_name, description) values
       ('pending', 'Phase is waiting to be run'),
       ('running', 'Phase is currently running'),
       ('done', 'Phase has completed successfully'),
       ('cancelled', 'Phase has been cancelled'),
       ('failed', 'Terminated due to irrecoverable error')
       ;

/* A media file is identified by a file extension. In the following table, we store all of the file extensions used */
drop table if exists file_extension;
create table file_extension (
       id smallint unsigned not null auto_increment,
       extension varchar(8) not null, /* file extension */
       primary key (id),
       index (extension)
) engine = innodb;

/**
 * A media file is only relevant to a specific data context. A data context
 * is defined by the higher-level specifiers (centre, pipeline, genotype, strain,
 * phenotyping procedure, the corresponding parameters and measurement id).
 */
drop table if exists media_file;
create table media_file (
       id bigint unsigned not null auto_increment,
       cid int unsigned not null, /* centre id */
       lid int unsigned not null, /* pipeline id */
       gid int unsigned not null, /* genotype id */
       sid int unsigned not null, /* strain id */
       pid int unsigned not null, /* procedure id */
       qid int unsigned not null,  /* parameter id */
       mid bigint unsigned not null, /* measurement identifier */
       phase_id smallint unsigned not null, /* download or processing phase */
       status_id smallint unsigned not null, /* status of the phase */
       url varchar(2048), /* the source URL from where the media was downloaded */
       checksum varchar(40), /* sha1 checksum of media file (also used for retrieval of image tiles) */
       extension_id smallint unsigned, /* media file extension */
       is_image tinyint, /* 1 if image media; otherwise, 0 */
       width int unsigned, /* image width (if image media) */
       height int unsigned, /* image height (if image media) */
       created datetime not null, /* when was this record created */
       last_update timestamp not null default current_timestamp on update current_timestamp,
       touched tinyint not null default 1, /* 1 if the URL is still valid */
       primary key (id),
       unique data_context (cid, lid, gid, sid, pid, qid, mid),
       index (url),
       index (checksum),
       index (mid),
       foreign key (extension_id) references file_extension(id) on update cascade on delete restrict,
       foreign key (phase_id) references phase(id) on update cascade on delete restrict,
       foreign key (status_id) references a_status(id) on update cascade on delete restrict
) engine = innodb;


/* End of MySQL script */
