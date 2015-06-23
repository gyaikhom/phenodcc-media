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
@Table(name = "PROCEDURE_", catalog = "phenodcc_raw", schema = "")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "AProcedure.findAll", query = "SELECT p FROM AProcedure p"),
    @NamedQuery(name = "AProcedure.findByHjid", query = "SELECT p FROM AProcedure p WHERE p.hjid = :hjid"),
    @NamedQuery(name = "AProcedure.findByProcedureid", query = "SELECT p FROM AProcedure p WHERE p.procedureid = :procedureid")})
public class AProcedure implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private Long hjid;
    @Size(max = 255)
    @Column(length = 255)
    private String procedureid;
    @OneToMany(mappedBy = "seriesmediaparameterProcedu0")
    private Collection<Seriesmediaparameter> seriesmediaparameterCollection;

    public AProcedure() {
    }

    public AProcedure(Long hjid) {
        this.hjid = hjid;
    }

    public Long getHjid() {
        return hjid;
    }

    public void setHjid(Long hjid) {
        this.hjid = hjid;
    }

    public String getProcedureid() {
        return procedureid;
    }

    public void setProcedureid(String procedureid) {
        this.procedureid = procedureid;
    }

    @XmlTransient
    @JsonIgnore
    public Collection<Seriesmediaparameter> getSeriesmediaparameterCollection() {
        return seriesmediaparameterCollection;
    }

    public void setSeriesmediaparameterCollection(Collection<Seriesmediaparameter> seriesmediaparameterCollection) {
        this.seriesmediaparameterCollection = seriesmediaparameterCollection;
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
        if (!(object instanceof AProcedure)) {
            return false;
        }
        AProcedure other = (AProcedure) object;
        if ((this.hjid == null && other.hjid != null) || (this.hjid != null && !this.hjid.equals(other.hjid))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "org.mousephenotype.dcc.media.entities.AProcedure[ hjid=" + hjid + " ]";
    }
    
}
