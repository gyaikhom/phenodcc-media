/*
 * Copyright 2013 Medical Research Council Harwell.
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
package org.mousephenotype.dcc.media.webservice;

import java.util.List;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlSeeAlso;
import javax.xml.bind.annotation.XmlType;
import org.mousephenotype.dcc.entities.overviews.MetadataGroupToValues;
import org.mousephenotype.dcc.media.entities.MediaFileDetail;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@XmlSeeAlso(MediaFileDetail.class)
@XmlType(propOrder = {"success", "total", "details"})
public class MediaFileDetailsPack extends AbstractRestResponse<MediaFileDetail> {

    private List<MetadataGroupToValues> metadataGroups;

    public MediaFileDetailsPack() {
    }

    public List<MetadataGroupToValues> getMetadataGroups() {
        return metadataGroups;
    }

    public void setMetadataGroups(List<MetadataGroupToValues> metadataGroups) {
        this.metadataGroups = metadataGroups;
    }

    @Override
    @XmlElement(name = "details")
    public List<MediaFileDetail> getDataSet() {
        return super.getDataSet();
    }
}
