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
@Table(name = "a_status", catalog = "phenodcc_media", schema = "",
    uniqueConstraints = {@UniqueConstraint(columnNames = {"short_name"})})
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "AStatus.findAll", query = "SELECT s FROM AStatus s"),
    @NamedQuery(name = "AStatus.findById", query = "SELECT s FROM AStatus s WHERE s.id = :id"),
    @NamedQuery(name = "AStatus.findByShortName", query = "SELECT s FROM AStatus s WHERE s.shortName = :shortName"),
    @NamedQuery(name = "AStatus.findByRgba", query = "SELECT s FROM AStatus s WHERE s.rgba = :rgba"),
    @NamedQuery(name = "AStatus.findByLastUpdate", query = "SELECT s FROM AStatus s WHERE s.lastUpdate = :lastUpdate")})
public class AStatus implements Serializable {

    private static final String DEFAULT_COLOR = "00000000"; /* black is the default */

    // required phase status (should correspond to the status table in the database)
    public static final String PENDING = "pending";
    public static final String RUNNING = "running";
    public static final String DONE = "done";
    public static final String CANCELLED = "cancelled";
    public static final String FAILED = "failed";
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
    @Column(nullable = false, length = 8)
    private String rgba;
    @Basic(optional = false)
    @Column(name = "last_update", columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", nullable = false, insertable = false, updatable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastUpdate;
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "statusId")
    private Collection<MediaFile> mediaFileCollection;

    public AStatus() {
    }

    public AStatus(String shortName) {
        this.shortName = shortName;
        this.rgba = DEFAULT_COLOR;
    }

    public AStatus(String shortName, String description) {
        this.shortName = shortName;
        this.description = description;
        this.rgba = DEFAULT_COLOR;
    }

    public AStatus(String shortName, String description, String rgba) {
        this.shortName = shortName;
        this.description = description;
        this.rgba = rgba;
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

    public String getRgba() {
        return rgba;
    }

    public void setRgba(String rgba) {
        this.rgba = rgba;
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
