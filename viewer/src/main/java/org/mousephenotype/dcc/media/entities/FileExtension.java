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
import javax.persistence.Basic;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
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
@Table(name = "file_extension", catalog = "phenodcc_media", schema = "")
@XmlRootElement
@NamedQueries({
    @NamedQuery(name = "FileExtension.findAll", query = "SELECT f FROM FileExtension f"),
    @NamedQuery(name = "FileExtension.findById", query = "SELECT f FROM FileExtension f WHERE f.id = :id"),
    @NamedQuery(name = "FileExtension.findByExtension", query = "SELECT f FROM FileExtension f WHERE f.extension = :extension")})
public class FileExtension implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Basic(optional = false)
    @Column(nullable = false)
    private Short id;
    @Basic(optional = false)
    @NotNull
    @Size(min = 1, max = 8)
    @Column(nullable = false, length = 8)
    private String extension;

    public FileExtension() {
    }

    public FileExtension(Short id) {
        this.id = id;
    }

    public FileExtension(Short id, String extension) {
        this.id = id;
        this.extension = extension;
    }

    public Short getId() {
        return id;
    }

    public void setId(Short id) {
        this.id = id;
    }

    public String getExtension() {
        return extension;
    }

    public void setExtension(String extension) {
        this.extension = extension;
    }
}
