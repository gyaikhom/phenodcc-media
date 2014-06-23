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
import java.util.Collection;
import java.util.Date;
import javax.persistence.Basic;
import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Lob;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToMany;
import javax.persistence.Table;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.persistence.UniqueConstraint;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@Entity
@Table(name = "phase", catalog = "phenodcc_media", schema = "",
    uniqueConstraints = {@UniqueConstraint(columnNames = {"short_name"})})
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "Phase.findAll", query = "SELECT p FROM Phase p"),
    @NamedQuery(name = "Phase.findById", query = "SELECT p FROM Phase p WHERE p.id = :id"),
    @NamedQuery(name = "Phase.findByShortName", query = "SELECT p FROM Phase p WHERE p.shortName = :shortName"),
    @NamedQuery(name = "Phase.findByLastUpdate", query = "SELECT p FROM Phase p WHERE p.lastUpdate = :lastUpdate")})
public class Phase implements Serializable {

    // required phases (should correspond to the phase table in the database)
    public static final String DOWNLOAD_FILE = "download";
    public static final String CHECK_ZIP_FILENAME = "zip_name";
    public static final String CHECK_ZIP_MD5 = "zip_md5"; /* not used */
    public static final String EXTRACT_XML = "unzip";
    public static final String CHECK_XML_FILENAME = "xml_name";
    public static final String VALIDATE_XML = "xsd";
    public static final String UPLOAD_DATA = "upload";
    public static final String CHECK_DATA_INTEGRITY = "data";
    public static final String BUILD_CONTEXT = "context";
    public static final String BUILD_OVERVIEWS = "overview";
    public static final String QC_DATA = "qc";

    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(nullable = false)
    private Short id;
    @Basic(optional = false)
    @Column(name = "short_name", nullable = false, length = 64)
    private String shortName;
    @Lob
    @Column(length = 65535)
    private String description;
    @Basic(optional = false)
    @Column(name = "last_update", columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", nullable = false, insertable = false, updatable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastUpdate;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "phaseId")
    private Collection<MediaFile> mediaFileCollection;

    public Phase() {
    }

    public Phase(String shortName) {
        this.shortName = shortName;
    }

    public Phase(String shortName, String description) {
        this.shortName = shortName;
        this.description = description;
    }

    public Short getId() {
        return id;
    }

    public void setId(Short id) {
        this.id = id;
    }

    public String getShortName() {
        return shortName;
    }

    public void setShortName(String shortName) {
        this.shortName = shortName;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Date getLastUpdate() {
        return lastUpdate;
    }

    public void setLastUpdate(Date lastUpdate) {
        this.lastUpdate = lastUpdate;
    }

    @XmlTransient
    public Collection<MediaFile> getMediaFileCollection() {
        return mediaFileCollection;
    }

    public void setMediaFileCollection(Collection<MediaFile> mediaFileCollection) {
        this.mediaFileCollection = mediaFileCollection;
    }
}
