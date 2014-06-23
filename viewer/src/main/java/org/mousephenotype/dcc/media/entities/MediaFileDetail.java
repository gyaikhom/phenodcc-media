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
import java.math.BigInteger;
import java.util.Date;
import javax.xml.bind.annotation.XmlElement;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
public class MediaFileDetail implements Serializable {

    private Long id;
    private Long measurementId;
    private BigInteger animalId;
    private String animalName;
    private Integer genotypeId;
    private Integer zygosity;
    private Integer sex;
    private Date startDate;
    private String equipmentManufacturer;
    private String equipmentModel;
    private final String checksum;
    private Integer isImage;
    private String extension;
    private Integer width;
    private Integer height;
    private final Short phase;
    private final Short status;
    private String metadataGroup;
    private Integer pipelineId;

    public MediaFileDetail(Long id, Long measurementId, BigInteger animalId,
            String animalName, Integer genotypeId, Integer zygosity,
            Integer sex, Date startDate, String equipmentManufacturer,
            String equipmentModel, String checksum, Integer isImage,
            String extension, Integer width, Integer height, Short phase,
            Short status, String metadataGroup, Integer pipelineId) {
        this.id = id;
        this.measurementId = measurementId;
        this.animalId = animalId;
        this.animalName = animalName;
        this.genotypeId = genotypeId;
        this.zygosity = zygosity;
        this.sex = sex;
        this.startDate = startDate;
        this.equipmentManufacturer = equipmentManufacturer;
        this.equipmentModel = equipmentModel;
        this.checksum = checksum;
        this.isImage = isImage;
        this.extension = extension;
        this.width = width;
        this.height = height;
        this.phase = phase;
        this.status = status;
        this.metadataGroup = metadataGroup;
        this.pipelineId = pipelineId;
    }

    @XmlElement(name = "id")
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    @XmlElement(name = "mid")
    public Long getMeasurementId() {
        return measurementId;
    }

    public void setMeasurementId(Long measurementId) {
        this.measurementId = measurementId;
    }

    @XmlElement(name = "aid")
    public BigInteger getAnimalId() {
        return animalId;
    }

    public void setAnimalId(BigInteger animalId) {
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

    @XmlElement(name = "em")
    public String getEquipmentManufacturer() {
        return equipmentManufacturer;
    }

    public void setEquipmentManufacturer(String equipmentManufacturer) {
        this.equipmentManufacturer = equipmentManufacturer;
    }

    @XmlElement(name = "en")
    public String getEquipmentModel() {
        return equipmentModel;
    }

    public void setEquipmentModel(String equipmentModel) {
        this.equipmentModel = equipmentModel;
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

    @XmlElement(name = "s")
    public Short getStatus() {
        return status;
    }

    @XmlElement(name = "m")
    public String getMetadataGroup() {
        return metadataGroup;
    }

    public void setMetadataGroup(String metadataGroup) {
        this.metadataGroup = metadataGroup;
    }

    @XmlElement(name = "lid")
    public Integer getPipelineId() {
        return pipelineId;
    }

    public void setPipelineId(Integer pipelineId) {
        this.pipelineId = pipelineId;
    }
}
