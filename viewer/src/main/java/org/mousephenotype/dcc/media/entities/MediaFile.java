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
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
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
@Table(name = "media_file", catalog = "phenodcc_media", schema = "", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"cid", "lid", "gid", "sid", "pid", "qid", "mid"})})
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "MediaFile.findAll", query = "SELECT m FROM MediaFile m"),
    @NamedQuery(name = "MediaFile.findById", query = "SELECT m FROM MediaFile m WHERE m.id = :id"),
    @NamedQuery(name = "MediaFile.findByCid", query = "SELECT m FROM MediaFile m WHERE m.cid = :cid"),
    @NamedQuery(name = "MediaFile.findByLid", query = "SELECT m FROM MediaFile m WHERE m.lid = :lid"),
    @NamedQuery(name = "MediaFile.findByGid", query = "SELECT m FROM MediaFile m WHERE m.gid = :gid"),
    @NamedQuery(name = "MediaFile.findBySid", query = "SELECT m FROM MediaFile m WHERE m.sid = :sid"),
    @NamedQuery(name = "MediaFile.findByPid", query = "SELECT m FROM MediaFile m WHERE m.pid = :pid"),
    @NamedQuery(name = "MediaFile.findByQid", query = "SELECT m FROM MediaFile m WHERE m.qid = :qid"),
    @NamedQuery(name = "MediaFile.findByMid", query = "SELECT m FROM MediaFile m WHERE m.mid = :mid"),
    @NamedQuery(name = "MediaFile.findByUrl", query = "SELECT m FROM MediaFile m WHERE m.url = :url"),
    @NamedQuery(name = "MediaFile.findByChecksum", query = "SELECT m FROM MediaFile m WHERE m.checksum = :checksum"),
    @NamedQuery(name = "MediaFile.findByCreated", query = "SELECT m FROM MediaFile m WHERE m.created = :created"),
    @NamedQuery(name = "MediaFile.findByLastUpdate", query = "SELECT m FROM MediaFile m WHERE m.lastUpdate = :lastUpdate"),
    @NamedQuery(name = "MediaFile.findByTouched", query = "SELECT m FROM MediaFile m WHERE m.touched = :touched"),
    @NamedQuery(name = "MediaFile.findMutantMediaFilesProcedurePipeline", query = "SELECT new org.mousephenotype.dcc.media.entities.MediaFileDetail(mf.id, mp.animalId, mp.animalName, mp.genotypeId, mp.zygosity, mp.sex, mp.startDate, mf.checksum, mf.isImage, e.extension, mf.width, mf.height, mf.phaseId.id, mf.statusId.id, mp.metadataGroup, l.pipelineId, p.procedureId, q.parameterId) FROM MeasurementsPerformed mp LEFT JOIN MediaFile mf ON (mf.mid = mp.measurementId) LEFT JOIN FileExtension e ON (e = mf.extensionId) LEFT JOIN ProcedureAnimalOverview pao ON (pao.procedureOccurrenceId = mp.procedureOccurrenceId) LEFT JOIN Procedure p ON (p.procedureKey = pao.procedureId) LEFT JOIN Pipeline l ON (l.pipelineKey = pao.pipeline) LEFT JOIN Parameter q ON (q.parameterKey = mp.parameterId) WHERE mp.centreId = :centreId AND mp.genotypeId = :genotypeId AND mp.strainId = :strainId AND mp.parameterId = :parameterKey AND p.procedureId = :procedureId AND l.pipelineId = :pipelineId ORDER BY mp.animalName"),
    @NamedQuery(name = "MediaFile.findBaselineMediaFilesProcedurePipeline", query = "SELECT new org.mousephenotype.dcc.media.entities.MediaFileDetail(mf.id, mp.animalId, mp.animalName, mp.genotypeId, mp.zygosity, mp.sex, mp.startDate, mf.checksum, mf.isImage, e.extension, mf.width, mf.height, mf.phaseId.id, mf.statusId.id, mp.metadataGroup, l.pipelineId, p.procedureId, q.parameterId) FROM MeasurementsPerformed mp LEFT JOIN MediaFile mf ON (mf.mid = mp.measurementId) LEFT JOIN FileExtension e ON (e = mf.extensionId) LEFT JOIN ProcedureAnimalOverview pao ON (pao.procedureOccurrenceId = mp.procedureOccurrenceId) LEFT JOIN Procedure p ON (p.procedureKey = pao.procedureId) LEFT JOIN Pipeline l ON (l.pipelineKey = pao.pipeline) LEFT JOIN Parameter q ON (q.parameterKey = mp.parameterId) WHERE mp.centreId = :centreId AND mp.genotypeId = 0 AND mp.strainId = :strainId AND mp.parameterId = :parameterKey AND mp.metadataGroup = :metadataGroup AND p.procedureId = :procedureId AND l.pipelineId = :pipelineId ORDER BY mp.animalName"),
    @NamedQuery(name = "MediaFile.findMutantMediaFiles", query = "SELECT new org.mousephenotype.dcc.media.entities.MediaFileDetail(mf.id, mp.animalId, mp.animalName, mp.genotypeId, mp.zygosity, mp.sex, mp.startDate, mf.checksum, mf.isImage, e.extension, mf.width, mf.height, mf.phaseId.id, mf.statusId.id, mp.metadataGroup, l.pipelineId, p.procedureId, q.parameterId) FROM MeasurementsPerformed mp LEFT JOIN MediaFile mf ON (mf.mid = mp.measurementId) LEFT JOIN FileExtension e ON (e = mf.extensionId) LEFT JOIN ProcedureAnimalOverview pao ON (pao.procedureOccurrenceId = mp.procedureOccurrenceId) LEFT JOIN Procedure p ON (p.procedureKey = pao.procedureId) LEFT JOIN Pipeline l ON (l.pipelineKey = pao.pipeline) LEFT JOIN Parameter q ON (q.parameterKey = mp.parameterId) WHERE mp.centreId = :centreId AND mp.genotypeId = :genotypeId AND mp.strainId = :strainId AND mp.parameterId = :parameterKey ORDER BY mp.animalName"),
    @NamedQuery(name = "MediaFile.findBaselineMediaFiles", query = "SELECT new org.mousephenotype.dcc.media.entities.MediaFileDetail(mf.id, mp.animalId, mp.animalName, mp.genotypeId, mp.zygosity, mp.sex, mp.startDate, mf.checksum, mf.isImage, e.extension, mf.width, mf.height, mf.phaseId.id, mf.statusId.id, mp.metadataGroup, l.pipelineId, p.procedureId, q.parameterId) FROM MeasurementsPerformed mp LEFT JOIN MediaFile mf ON (mf.mid = mp.measurementId) LEFT JOIN FileExtension e ON (e = mf.extensionId) LEFT JOIN ProcedureAnimalOverview pao ON (pao.procedureOccurrenceId = mp.procedureOccurrenceId) LEFT JOIN Procedure p ON (p.procedureKey = pao.procedureId) LEFT JOIN Pipeline l ON (l.pipelineKey = pao.pipeline) LEFT JOIN Parameter q ON (q.parameterKey = mp.parameterId) WHERE mp.centreId = :centreId AND mp.genotypeId = 0 AND mp.strainId = :strainId AND mp.parameterId = :parameterKey AND mp.metadataGroup = :metadataGroup ORDER BY mp.animalName")
})
public class MediaFile implements Serializable {

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
    private int qid;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private long mid;
    @Size(max = 2048)
    @Column(length = 2048)
    private String url;
    @Size(max = 40)
    @Column(length = 40)
    private String checksum;
    @Basic(optional = true)
    @Column(name = "is_image", nullable = true)
    private int isImage;
    @Basic(optional = true)
    @Column(nullable = true)
    private int width;
    @Basic(optional = true)
    @Column(nullable = true)
    private int height;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date created;
    @Basic(optional = false)
    @NotNull
    @Column(name = "last_update", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastUpdate;
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private short touched;
    @JoinColumn(name = "status_id", referencedColumnName = "id", nullable = false)
    @ManyToOne(optional = false)
    private AStatus statusId;
    @JoinColumn(name = "phase_id", referencedColumnName = "id", nullable = false)
    @ManyToOne(optional = false)
    private Phase phaseId;
    @JoinColumn(name = "extension_id", referencedColumnName = "id", nullable = true)
    @ManyToOne(optional = true)
    private FileExtension extensionId;

    public MediaFile() {
    }

    public MediaFile(Long id) {
        this.id = id;
    }

    public MediaFile(Long id, int cid, int lid, int gid, int sid, int pid,
            int qid, long mid, Date created, Date lastUpdate, short touched) {
        this.id = id;
        this.cid = cid;
        this.lid = lid;
        this.gid = gid;
        this.sid = sid;
        this.pid = pid;
        this.qid = qid;
        this.mid = mid;
        this.created = created;
        this.lastUpdate = lastUpdate;
        this.touched = touched;
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

    public int getQid() {
        return qid;
    }

    public void setQid(int qid) {
        this.qid = qid;
    }

    public long getMid() {
        return mid;
    }

    public void setMid(long mid) {
        this.mid = mid;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getChecksum() {
        return checksum;
    }

    public void setChecksum(String checksum) {
        this.checksum = checksum;
    }

    public int getIsImage() {
        return isImage;
    }

    public void setIsImage(int isImage) {
        this.isImage = isImage;
    }

    public int getWidth() {
        return width;
    }

    public void setWidth(int width) {
        this.width = width;
    }

    public int getHeight() {
        return height;
    }

    public void setHeight(int height) {
        this.height = height;
    }

    public Date getCreated() {
        return created;
    }

    public void setCreated(Date created) {
        this.created = created;
    }

    public Date getLastUpdate() {
        return lastUpdate;
    }

    public void setLastUpdate(Date lastUpdate) {
        this.lastUpdate = lastUpdate;
    }

    public short getTouched() {
        return touched;
    }

    public void setTouched(short touched) {
        this.touched = touched;
    }

    public AStatus getStatusId() {
        return statusId;
    }

    public void setStatusId(AStatus statusId) {
        this.statusId = statusId;
    }

    public Phase getPhaseId() {
        return phaseId;
    }

    public void setPhaseId(Phase phaseId) {
        this.phaseId = phaseId;
    }

    public FileExtension getExtensionId() {
        return extensionId;
    }

    public void setExtensionId(FileExtension extensionId) {
        this.extensionId = extensionId;
    }
}
