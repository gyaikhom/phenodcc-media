/*
 * Copyright 2014 Medical Research Council Harwell.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.mousephenotype.dcc.media.entities;

import java.io.Serializable;
import java.util.Date;
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.persistence.UniqueConstraint;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@Entity
@Table(name = "association", catalog = "phenodcc_media", schema = "", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"cid", "lid", "gid", "sid", "pid", "mid", "media_qid", "assoc_qid"})})
@XmlRootElement
public class Association implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(nullable = false)
    private Long id;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private int cid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private int lid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private int gid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private int sid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private int pid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private long mid;
    @Basic(optional = false)
    @NotNull
    @Column(name = "media_qid", nullable = false)
    private int mediaQid;
    @Basic(optional = false)
    @NotNull
    @Column(name = "assoc_qid", nullable = false)
    private int assocQid;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 32)
    @Column(name = "assoc_qeid", nullable = false, length = 32)
    private String assocQeid;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 512)
    @Column(name = "assoc_name", nullable = false, length = 512)
    private String assocName;
    @Basic(optional = false)
    @NotNull
    @Column(name = "last_update", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastUpdate;

    public Association() {
    }

    public Association(Long id) {
        this.id = id;
    }

    public Association(Long id, int cid, int lid, int gid, int sid, int pid,
            long mid, int mediaQid, int assocQid, String assocQeid,
            String assocName, Date lastUpdate) {
        this.id = id;
        this.cid = cid;
        this.lid = lid;
        this.gid = gid;
        this.sid = sid;
        this.pid = pid;
        this.mid = mid;
        this.mediaQid = mediaQid;
        this.assocQid = assocQid;
        this.assocQeid = assocQeid;
        this.assocName = assocName;
        this.lastUpdate = lastUpdate;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public int getCid() {
        return cid;
    }

    public void setCid(int cid) {
        this.cid = cid;
    }

    public int getLid() {
        return lid;
    }

    public void setLid(int lid) {
        this.lid = lid;
    }

    public int getGid() {
        return gid;
    }

    public void setGid(int gid) {
        this.gid = gid;
    }

    public int getSid() {
        return sid;
    }

    public void setSid(int sid) {
        this.sid = sid;
    }

    public int getPid() {
        return pid;
    }

    public void setPid(int pid) {
        this.pid = pid;
    }

    public long getMid() {
        return mid;
    }

    public void setMid(long mid) {
        this.mid = mid;
    }

    public int getMediaQid() {
        return mediaQid;
    }

    public void setMediaQid(int mediaQid) {
        this.mediaQid = mediaQid;
    }

    public int getAssocQid() {
        return assocQid;
    }

    public void setAssocQid(int assocQid) {
        this.assocQid = assocQid;
    }

    public String getAssocQeid() {
        return assocQeid;
    }

    public void setAssocQeid(String assocQeid) {
        this.assocQeid = assocQeid;
    }

    public String getAssocName() {
        return assocName;
    }

    public void setAssocName(String assocName) {
        this.assocName = assocName;
    }

    public Date getLastUpdate() {
        return lastUpdate;
    }

    public void setLastUpdate(Date lastUpdate) {
        this.lastUpdate = lastUpdate;
    }
    
}
