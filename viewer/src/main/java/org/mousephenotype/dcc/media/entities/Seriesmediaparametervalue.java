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
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;
import javax.xml.bind.annotation.XmlRootElement;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@Entity
@Table(name = "SERIESMEDIAPARAMETERVALUE", catalog = "phenodcc_raw", schema = "")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "Seriesmediaparametervalue.findAll", query = "SELECT s FROM Seriesmediaparametervalue s"),
    @NamedQuery(name = "Seriesmediaparametervalue.findByHjid", query = "SELECT s FROM Seriesmediaparametervalue s WHERE s.hjid = :hjid"),
    @NamedQuery(name = "Seriesmediaparametervalue.findByUri", query = "SELECT s FROM Seriesmediaparametervalue s WHERE s.uri = :uri"),
    @NamedQuery(name = "Seriesmediaparametervalue.findByFiletype", query = "SELECT s FROM Seriesmediaparametervalue s WHERE s.filetype = :filetype"),
    @NamedQuery(name = "Seriesmediaparametervalue.findByIncrementvalue", query = "SELECT s FROM Seriesmediaparametervalue s WHERE s.incrementvalue = :incrementvalue"),
    @NamedQuery(name = "Seriesmediaparametervalue.findByLink", query = "SELECT s FROM Seriesmediaparametervalue s WHERE s.link = :link"),
    @NamedQuery(name = "Seriesmediaparametervalue.getLink", query = "SELECT s.link FROM Seriesmediaparametervalue s WHERE s.hjid = :hjid")
})
public class Seriesmediaparametervalue implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id
    @Basic(optional = false)
    @NotNull
    @Column(nullable = false)
    private Long hjid;
    @Size(max = 255)
    @Column(length = 255)
    private String uri;
    @Size(max = 255)
    @Column(length = 255)
    private String filetype;
    @Size(max = 255)
    @Column(length = 255)
    private String incrementvalue;
    @Size(max = 255)
    @Column(length = 255)
    private String link;
    @JoinColumn(name = "VALUE__SERIESMEDIAPARAMETER__0", referencedColumnName = "HJID")
    @ManyToOne
    private Seriesmediaparameter valueSeriesmediaparameter0;

    public Seriesmediaparametervalue() {
    }

    public Seriesmediaparametervalue(Long hjid) {
        this.hjid = hjid;
    }

    public Long getHjid() {
        return hjid;
    }

    public void setHjid(Long hjid) {
        this.hjid = hjid;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getFiletype() {
        return filetype;
    }

    public void setFiletype(String filetype) {
        this.filetype = filetype;
    }

    public String getIncrementvalue() {
        return incrementvalue;
    }

    public void setIncrementvalue(String incrementvalue) {
        this.incrementvalue = incrementvalue;
    }

    public String getLink() {
        return link;
    }

    public void setLink(String link) {
        this.link = link;
    }

    public Seriesmediaparameter getValueSeriesmediaparameter0() {
        return valueSeriesmediaparameter0;
    }

    public void setValueSeriesmediaparameter0(Seriesmediaparameter valueSeriesmediaparameter0) {
        this.valueSeriesmediaparameter0 = valueSeriesmediaparameter0;
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
        if (!(object instanceof Seriesmediaparametervalue)) {
            return false;
        }
        Seriesmediaparametervalue other = (Seriesmediaparametervalue) object;
        if ((this.hjid == null && other.hjid != null) || (this.hjid != null && !this.hjid.equals(other.hjid))) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "org.mousephenotype.dcc.media.entities.Seriesmediaparametervalue[ hjid=" + hjid + " ]";
    }
    
}
