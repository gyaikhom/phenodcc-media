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


/* For every phase (e.g., download and processing), we wish to record reasons for failure. This is captured here by capturing the runtime Python exceptions. */
drop table if exists error_logs;
create table error_logs (
       id bigint unsigned not null auto_increment,
       media_id bigint unsigned not null, /* primary key of media file */
       phase_id smallint unsigned not null, /* at which phase did the error occur */
       error_msg varchar(256), /* Python error message extracted from the exception (column name corresponds to Python)*/
       created datetime not null, /* when was this error recorded */
       last_update timestamp not null default current_timestamp on update current_timestamp,
       primary key (id),
       foreign key (media_id) references media_file(id) on update cascade on delete restrict,
       foreign key (phase_id) references phase(id) on update cascade on delete restrict
) engine = innodb;

/* A media file could be associated with other measurements. These are supplied by the centres as parameter associations. In the following table, we store all of the parameters which a media is associated with. A media file may be associated with more than one parameter. All associations are implicitly restricted to parameters with measurements with the same context, i.e., centre, pipeline, genotype, strain.

The following table is design with two usage scenarios in mind:

1) Given a measurement context, show the media related to this context.
2) Given a media context, show all of the parameters with which it is associated.
3) Given a specific media, show parameter it is associated with. This is used for displaying media labels. 

This table is filled in after the media_file has been updated during context building, especially during media downloader prepare phase. See parameter_association.md for further details. */
drop table if exists association;
create table association (
       id bigint unsigned not null auto_increment,
       cid int unsigned not null, /* centre id */
       lid int unsigned not null, /* pipeline id */
       gid int unsigned not null, /* genotype id */
       sid int unsigned not null, /* strain id */
       pid int unsigned not null, /* procedure id */
       mid bigint unsigned not null,  /* measurement id associated with media file */
       media_qid int unsigned not null,  /* id for media parameter */
       assoc_qid int unsigned not null,  /* id for associated parameter */

       /* following are useful for display */
       assoc_qeid varchar(32) not null,  /* key for associated parameter */
       assoc_name varchar(512) not null,  /* name for associated parameter */
       last_update timestamp not null default current_timestamp on update current_timestamp,
       primary key (id),
       unique parameter_assoc_idx (cid, lid, gid, sid, pid, mid, media_qid, assoc_qid),
       index gene_context_idx (cid, lid, gid, sid),
       index measurement_idx (mid),
       index procedure_idx (pid),
       index media_qid_idx (media_qid),
       index assoc_qid_idx (assoc_qid)
) engine = innodb;

/* End of MySQL script */
