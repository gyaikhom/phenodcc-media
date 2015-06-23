/*
 * Copyright 2015 Medical Research Council Harwell.
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
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToMany;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import org.codehaus.jackson.annotate.JsonIgnore;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@Entity
@Table(name = "SERIESMEDIAPARAMETER", catalog = "phenodcc_raw", schema = "")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "Seriesmediaparameter.findAll", query = "SELECT s FROM Seriesmediaparameter s"),
    @NamedQuery(name = "Seriesmediaparameter.findByHjid", query = "SELECT s FROM Seriesmediaparameter s WHERE s.hjid = :hjid"),
    @NamedQuery(name = "Seriesmediaparameter.findByParameterid", query = "SELECT s FROM Seriesmediaparameter s WHERE s.parameterid = :parameterid"),
    @NamedQuery(name = "Seriesmediaparameter.findByParameterstatus", query = "SELECT s FROM Seriesmediaparameter s WHERE s.parameterstatus = :parameterstatus")})
public class Seriesmediaparameter implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private Long hjid;
    @Size(max = 255)
    @Column(length = 255)
    private String parameterid;
    @Size(max = 255)
    @Column(length = 255)
    private String parameterstatus;
    @OneToMany(mappedBy = "valueSeriesmediaparameter0")
    private Collection<Seriesmediaparametervalue> seriesmediaparametervalueCollection;
    @JoinColumn(name = "SERIESMEDIAPARAMETER_PROCEDU_0", referencedColumnName = "HJID")
    @ManyToOne
    private AProcedure seriesmediaparameterProcedu0;

    public Seriesmediaparameter() {
    }

    public Seriesmediaparameter(Long hjid) {
        this.hjid = hjid;
    }

    public Long getHjid() {
        return hjid;
    }

    public void setHjid(Long hjid) {
        this.hjid = hjid;
    }

    public String getParameterid() {
        return parameterid;
    }

    public void setParameterid(String parameterid) {
        this.parameterid = parameterid;
    }

    public String getParameterstatus() {
        return parameterstatus;
    }

    public void setParameterstatus(String parameterstatus) {
        this.parameterstatus = parameterstatus;
    }

    @XmlTransient
    @JsonIgnore
    public Collection<Seriesmediaparametervalue> getSeriesmediaparametervalueCollection() {
        return seriesmediaparametervalueCollection;
    }

    public void setSeriesmediaparametervalueCollection(Collection<Seriesmediaparametervalue> seriesmediaparametervalueCollection) {
        this.seriesmediaparametervalueCollection = seriesmediaparametervalueCollection;
    }

    public AProcedure getSeriesmediaparameterProcedu0() {
        return seriesmediaparameterProcedu0;
    }

    public void setSeriesmediaparameterProcedu0(AProcedure seriesmediaparameterProcedu0) {
        this.seriesmediaparameterProcedu0 = seriesmediaparameterProcedu0;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (hjid != null ? hjid.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        // TODO: Warning - this method won't work in the case the id fields are not set
        if (!(object instanceof Seriesmediaparameter)) {
            return false;
        }
        Seriesmediaparameter other = (Seriesmediaparameter) object;
        if ((this.hjid == null && other.hjid != null) || (this.hjid != null && !this.hjid.equals(other.hjid))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "org.mousephenotype.dcc.media.entities.Seriesmediaparameter[ hjid=" + hjid + " ]";
    }
    
}
