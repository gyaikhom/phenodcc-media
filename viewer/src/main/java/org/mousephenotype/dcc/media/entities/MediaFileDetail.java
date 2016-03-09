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
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlTransient;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
public class MediaFileDetail implements Serializable {

    private Long id;
    private Integer animalId;
    private String animalName;
    private Integer genotypeId;
    private Integer zygosity;
    private Integer sex;
    private Date startDate;
    private final String checksum;
    private Integer isImage;
    private String extension;
    private Integer width;
    private Integer height;
    private Short phase;
    private Short status;
    private String metadataGroup;
    private Long metadataGroupIndex;
    private Integer pipelineId;
    private Integer procedureId;
    private Integer parameterId;
    private Long measurementId;
    private String associatedParameterKey;
    private String associatedParameterName;
    private String link;

    public MediaFileDetail(Long id, Integer animalId, String animalName,
            Integer genotypeId, Integer zygosity, Integer sex, Date startDate,
            String checksum, Integer isImage, String extension, Integer width,
            Integer height, Short phase, Short status, String metadataGroup,
            Integer pipelineId, Integer procedureId, Integer parameterId,
            Long measurementId, String associatedParameterKey,
            String associatedParameterName, String link) {
        this.id = id;
        this.animalId = animalId;
        this.animalName = animalName;
        this.genotypeId = genotypeId;
        this.zygosity = zygosity;
        this.sex = sex;
        this.startDate = startDate;
        this.checksum = checksum;
        this.isImage = isImage;
        this.extension = extension;
        this.width = width;
        this.height = height;
        this.phase = phase;
        this.status = status;
        this.metadataGroup = metadataGroup;
        this.pipelineId = pipelineId;
        this.procedureId = procedureId;
        this.parameterId = parameterId;
        this.measurementId = measurementId;
        this.associatedParameterKey = associatedParameterKey;
        this.associatedParameterName = associatedParameterName;
        this.link = link;
    }

    @XmlElement(name = "id")
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    @XmlElement(name = "aid")
    public Integer getAnimalId() {
        return animalId;
    }

    public void setAnimalId(Integer animalId) {
        this.animalId = animalId;
    }

    @XmlElement(name = "an")
    public String getAnimalName() {
        return animalName;
    }

    public void setAnimalName(String animalName) {
        this.animalName = animalName;
    }

    @XmlElement(name = "gid")
    public Integer getGenotypeId() {
        return genotypeId;
    }

    public void setGenotypeId(Integer genotypeId) {
        this.genotypeId = genotypeId;
    }

    @XmlElement(name = "z")
    public Integer getZygosity() {
        return zygosity;
    }

    public void setZygosity(Integer zygosity) {
        this.zygosity = zygosity;
    }

    @XmlElement(name = "g")
    public Integer getSex() {
        return sex;
    }

    public void setSex(Integer sex) {
        this.sex = sex;
    }

    @XmlElement(name = "d")
    public Date getStartDate() {
        return startDate;
    }

    public void setStartDate(Date startDate) {
        this.startDate = startDate;
    }

    @XmlElement(name = "c")
    public String getChecksum() {
        return checksum;
    }

    @XmlElement(name = "i")
    public Integer getIsImage() {
        return isImage;
    }

    public void setIsImage(Integer isImage) {
        this.isImage = isImage;
    }

    @XmlElement(name = "e")
    public String getExtension() {
        return extension;
    }

    public void setExtension(String extension) {
        this.extension = extension;
    }

    @XmlElement(name = "w")
    public Integer getWidth() {
        return width;
    }

    public void setWidth(Integer width) {
        this.width = width;
    }

    @XmlElement(name = "h")
    public Integer getHeight() {
        return height;
    }

    public void setHeight(Integer height) {
        this.height = height;
    }

    @XmlElement(name = "p")
    public Short getPhase() {
        return phase;
    }

    public void setPhase(Short phase) {
        this.phase = phase;
    }

    @XmlElement(name = "s")
    public Short getStatus() {
        return status;
    }

    public void setStatus(Short status) {
        this.status = status;
    }

    @XmlTransient
    public String getMetadataGroup() {
        return metadataGroup;
    }

    public void setMetadataGroup(String metadataGroup) {
        this.metadataGroup = metadataGroup;
    }

    @XmlElement(name = "m")
    public Long getMetadataGroupIndex() {
        return metadataGroupIndex;
    }

    public void setMetadataGroupIndex(Long metadataGroupIndex) {
        this.metadataGroupIndex = metadataGroupIndex;
    }

    @XmlElement(name = "lid")
    public Integer getPipelineId() {
        return pipelineId;
    }

    public void setPipelineId(Integer pipelineId) {
        this.pipelineId = pipelineId;
    }

    @XmlElement(name = "pid")
    public Integer getProcedureId() {
        return procedureId;
    }

    public void setProcedureId(Integer procedureId) {
        this.procedureId = procedureId;
    }

    @XmlElement(name = "qid")
    public Integer getParameterId() {
        return parameterId;
    }

    public void setParameterId(Integer parameterId) {
        this.parameterId = parameterId;
    }

    @XmlElement(name = "mid")
    public Long getMeasurementId() {
        return measurementId;
    }

    public void setMeasurementId(Long measurementId) {
        this.measurementId = measurementId;
    }

    @XmlElement(name = "k")
    public String getAssociatedParameterKey() {
        return associatedParameterKey;
    }

    public void setAssociatedParameterKey(String associatedParameterKey) {
        this.associatedParameterKey = associatedParameterKey;
    }

    @XmlElement(name = "n")
    public String getAssociatedParameterName() {
        return associatedParameterName;
    }

    public void setAssociatedParameterName(String associatedParameterName) {
        this.associatedParameterName = associatedParameterName;
    }

    @XmlElement(name = "l")
    public String getLink() {
        return link;
    }

    public void setLink(String link) {
        this.link = link;
    }

}
