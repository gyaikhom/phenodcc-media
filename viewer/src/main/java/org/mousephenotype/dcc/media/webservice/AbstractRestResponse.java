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
package org.mousephenotype.dcc.media.webservice;

import java.util.ArrayList;
import java.util.List;
import javax.xml.bind.annotation.XmlRootElement;

/**
 * Provides methods that are common to response handlers for all of the
 * RESTful web services.
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 * @param <T>
 */
@XmlRootElement
public abstract class AbstractRestResponse<T> {

    private boolean success = false;
    private long total = 0L; /* if negative, absolute value gives error code */
    private List<T> dataSet = null;

    public AbstractRestResponse() {
    }

    public List<T> getDataSet() {
        return dataSet;
    }

    public void setDataSet(List<T> dataSet) {
        this.dataSet = dataSet;
        if (dataSet == null || dataSet.isEmpty()) {
            this.success = false;
            this.dataSet = new ArrayList<>();
        } else {
            this.success = true;
            this.total = dataSet.size();
        }
    }

    public void setDataSet(List<T> dataSet, long total) {
        this.dataSet = dataSet;
        if (dataSet == null || dataSet.isEmpty()) {
            this.success = false;
            this.dataSet = new ArrayList<>();
        } else {
            this.success = true;
            this.total = total;
        }
    }

    public boolean getSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

}
