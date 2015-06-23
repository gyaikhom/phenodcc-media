# The design of the parameter association table.

A media file could be associated with other measurements. These are
supplied by the centres as parameter associations. In the following
table, we store all of the parameters which a media is associated
with. A media file may be associated with more than one parameter. All
associations are implicitly restricted to parameters with measurements
with the same context, i.e., centre, pipeline, genotype, strain.

The following table is design with two usage scenarios in mind:

1) Given a measurement context, show the media related to this context.
2) Given a media context, show all of the parameters with which it is
   associated.
3) Given a specific media, show parameter it is associated with. This
   is used for displaying media labels.

This table is filled in after the media_file has been updated during
context building, especially during media downloader prepare phase.

# Populating the table

To fill the table we use the following logic:

1) Truncate this table.
2) For every media file that is currently active, add the association records:

   a) Get all of the parameter ids from the phenodcc_raw.PARAMETERASSOCIATION
      table using this media's measurement id. We need to match this with
      either of the following columns in phenodcc_raw.PARAMETERASSOCIATION:

      I. PARAMETERASSOCIATION_SERIESM_0 (HJID of SERIESMEDIAPARAMETERVALUE),
      II. PARAMETERASSOCIATION_MEDIAPA_0 (HJID of MEDIAPARAMETER),
      III. PARAMETERASSOCIATION_MEDIAFI_0 (HJID of MEDIAFILE)

   b) For each parameter id from the set:

      I. find all active data context with the same parameter id from
         phenodcc_qc.data_context where cid, lid, gid and sid matches
         the context for the media and there are measurements. We could
         have simply stored the parameter id into the association without
         checking, however, this will include associations without
         measurements. Only including those with measurements prevents
         confusion and disappointment for the user.

      II. if a record already exists, goto b).

      III. if a record does not exists, add a record to mark the association.

3) Done filling table


# MySQL statements

The table can be populated using the following MySQL statements:

    use phenodcc_media;
    truncate association; /* clear out the assocation table */
    insert into association(cid, lid, gid, sid, mid, pid, media_qid, assoc_qid, assoc_qeid, assoc_name)
    select distinct
        /* following are common to media file and associated parameter */
        m.cid, /* centre_id */
        m.lid, /* pipeline id */
        m.gid, /* genotype id */
        m.sid, /* strain id */

        /* procedure and parameter for media file */
        m.mid, /* measurement id of the media file */
        m.pid, /* procedure id */
        m.qid, /* media parameter id */

        /* parameter to associate with the above media */
        ap.parameter_id,
        ap.parameter_key,
        ap.`name`
    from
        media_file as m
        left join `a_status` as s on (s.id = m.status_id)
        left join `phase` as p on (p.id = m.phase_id)
        inner join phenodcc_overviews.measurements_performed as mp on (mp.measurement_id = m.mid)
        right join phenodcc_raw.PARAMETERASSOCIATION as pa on (pa.PARAMETERASSOCIATION_SERIESM_0 = m.mid)
        left join impress.parameter as ap on (ap.parameter_key = pa.PARAMETERID)
    where
        s.short_name = 'done'
        and (p.short_name = 'checksum' or p.short_name = 'tile')
    ;


# Retrieving all contexts and parameter details

For a given media file context, the following MySQL query returns the
corresponding parameter association contexts and the parameter
details. This can be displayed next to a media file, or inside the
image viewer.

    # get all of the parameter contexts associated with a media file context
    select ctx.cid, ctx.lid, ctx.gid, ctx.sid, ctx.pid,
        ctx.qid as assoc_qid,
        aq.parameter_key as assoc_key,
        aq.`name` as assoc_name
    from
        phenodcc_media.association as a
        left join impress.parameter as aq on (aq.parameter_id = a.assoc_qid)
        left join phenodcc_qc.data_context as ctx on (
            ctx.cid = a.cid
            and ctx.lid = a.lid
            and ctx.gid = a.gid
            and ctx.sid = a.sid
            and ctx.qid = a.assoc_qid
        )
    where
        a.cid = 11
        and a.lid = 13
        and a.gid = 39
        and a.sid = 19
        and a.pid = 107
        and a.media_qid = 2577
    ;

For a given parameter context, the following MySQL query returns the
corresponding media file context and the parameter detail with which
it is associated. This can be used in parameter visualisations to add
a display media in image viewer.

    /* get the media file context associated with a parameter context */
    select a.cid, a.lid, a.gid, a.sid, a.pid, a.media_qid,
        mq.parameter_key as media_key,
        mq.`name` as media_name
    from
        phenodcc_media.association as a
        left join impress.parameter as mq on (mq.parameter_id = a.media_qid)
    where
        a.cid = 11
        and a.lid = 13
        and a.gid = 39
        and a.sid = 19
        and a.assoc_qid = 2504
    ;

