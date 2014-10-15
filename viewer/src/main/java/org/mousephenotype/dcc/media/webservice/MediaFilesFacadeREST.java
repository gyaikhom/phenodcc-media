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
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.TypedQuery;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import org.mousephenotype.dcc.entities.overviews.MetadataGroupToValues;
import org.mousephenotype.dcc.entities.overviews.ProcedureMetadataGroup;
import org.mousephenotype.dcc.media.entities.MediaFileDetail;

/**
 * Web service for retrieving media files for a given data context.
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
@Stateless
@Path("mediafiles")
public class MediaFilesFacadeREST extends AbstractFacade<MediaFileDetail> {

    public MediaFilesFacadeREST() {
        super(MediaFileDetail.class);
    }

    private List<MediaFileDetail> getMutantMediaFiles(
            Integer centreId,
            Integer genotypeId,
            Integer strainId,
            String parameterKey,
            Integer pipelineId,
            Integer procedureId) {
        EntityManager em = getEntityManager();
        List<MediaFileDetail> temp = new ArrayList<>();
        try {
            String namedQuery = "MediaFile.findMutantMediaFiles";
            if (pipelineId != null && procedureId != null) {
                namedQuery += "ProcedurePipeline";
            }
            TypedQuery<MediaFileDetail> query
                    = em.createNamedQuery(namedQuery, MediaFileDetail.class);
            query.setParameter("centreId", centreId);
            query.setParameter("genotypeId", genotypeId);
            query.setParameter("strainId", strainId);
            query.setParameter("parameterKey", parameterKey);
            if (pipelineId != null && procedureId != null) {
                query.setParameter("procedureId", procedureId);
                query.setParameter("pipelineId", pipelineId);
            }
            temp = query.getResultList();
        } catch (Exception e) {
            System.err.println(e.getMessage());
        } finally {
            em.close();
        }
        return temp;
    }

    private List<MediaFileDetail> getBaselineMediaFiles(
            Integer centreId,
            Integer strainId,
            String parameterKey,
            ProcedureMetadataGroup t,
            Integer pipelineId,
            Integer procedureId) {
        EntityManager em = getEntityManager();
        List<MediaFileDetail> temp = new ArrayList<>();
        try {
            String namedQuery = "MediaFile.findBaselineMediaFiles";
            if (pipelineId != null && procedureId != null) {
                namedQuery += "ProcedurePipeline";
            }
            TypedQuery<MediaFileDetail> query
                    = em.createNamedQuery(namedQuery, MediaFileDetail.class);
            query.setParameter("centreId", centreId);
            query.setParameter("strainId", strainId);
            query.setParameter("parameterKey", parameterKey);
            query.setParameter("metadataGroup", t.getMetadataGroup());
            if (pipelineId != null && procedureId != null) {
                query.setParameter("procedureId", procedureId);
                query.setParameter("pipelineId", pipelineId);
            }
            temp = query.getResultList();
        } catch (Exception e) {
            System.err.println(e.getMessage());
        } finally {
            em.close();
        }
        return temp;
    }

    private MetadataGroupToValues getMetadataGroupValue(String mg) {
        MetadataGroupToValues v = null;
        EntityManager em = getEntityManager();
        try {
            TypedQuery<MetadataGroupToValues> query
                    = em.createNamedQuery(
                            "MetadataGroupToValues.findByMetadataGroup",
                            MetadataGroupToValues.class);
            query.setParameter("metadataGroup", mg);
            query.setMaxResults(1);
            v = query.getSingleResult();
        } catch (Exception e) {
            System.err.println(e.getMessage());
        } finally {
            em.close();
        }
        return v;
    }

    // We do not wish to send the meta-data group checksum or the values
    // for every measurement. So, we group all of the distinct meta-data groups
    // and send them with the measurements. Within each measurement, we replace
    // the meta-data group checksum with the id.
    private List<MetadataGroupToValues> convertMetadataGroupsToIndices(List<MediaFileDetail> g) {
        List<MetadataGroupToValues> mgs = new ArrayList<>();
        HashMap<String, MetadataGroupToValues> distinct = new HashMap<>();
        Iterator<MediaFileDetail> i = g.iterator();
        while (i.hasNext()) {
            MediaFileDetail v = i.next();
            String checksum = v.getMetadataGroup();
            MetadataGroupToValues mg = distinct.get(checksum);
            if (mg == null) {
                mg = getMetadataGroupValue(checksum);
                if (mg != null) {
                    distinct.put(checksum, mg);
                    mgs.add(mg);
                }
            }
            v.setMetadataGroupIndex(mg == null
                    ? -1L : mg.getMetadataGroupToValuesId());
        }
        return mgs;
    }

    public List<ProcedureMetadataGroup> getProcedureMetadataGroups(
            Integer centreId,
            Integer genotypeId,
            Integer strainId,
            String parameterKey) {
        List<ProcedureMetadataGroup> t = null;
        EntityManager em = getEntityManager();
        try {
            TypedQuery<ProcedureMetadataGroup> q
                    = em.createNamedQuery("ProcedureAnimalOverview.findByCidGidSidQeid",
                            ProcedureMetadataGroup.class);
            q.setParameter("centreId", centreId);
            q.setParameter("genotypeId", genotypeId);
            q.setParameter("strainId", strainId);
            q.setParameter("parameterId", parameterKey);
            t = q.getResultList();
        } catch (Exception e) {
            System.err.println(e.getMessage());
        } finally {
            em.close();
        }
        return t;
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public MediaFileDetailsPack extjsFindBy(
            @QueryParam("cid") Integer centreId,
            @QueryParam("lid") Integer pipelineId,
            @QueryParam("gid") Integer genotypeId,
            @QueryParam("sid") Integer strainId,
            @QueryParam("pid") Integer procedureId,
            @QueryParam("qeid") String parameterKey,
            @QueryParam("includeBaseline") Boolean includeBaseline) {
        MediaFileDetailsPack p = new MediaFileDetailsPack();
        if (centreId == null || genotypeId == null || strainId == null
                || parameterKey == null || parameterKey.isEmpty()) {
            p.setDataSet(null, 0L);
        } else {
            List<ProcedureMetadataGroup> t = getProcedureMetadataGroups(
                    centreId, genotypeId, strainId, parameterKey);
            if (t == null || t.isEmpty()) {
                p.setDataSet(null, 0L);
            } else {
                List<MediaFileDetail> temp
                        = getMutantMediaFiles(centreId, genotypeId,
                                strainId, parameterKey, pipelineId, procedureId);
                ProcedureMetadataGroup mg = null;
                if (genotypeId != 0 && includeBaseline != null && includeBaseline) {
                    Iterator<ProcedureMetadataGroup> i = t.iterator();
                    while (i.hasNext()) {
                        mg = i.next();
                        temp.addAll(getBaselineMediaFiles(centreId, strainId, parameterKey, mg, pipelineId, procedureId));
                    }
                }
                List<MetadataGroupToValues> mgs = convertMetadataGroupsToIndices(temp);
                p.setMetadataGroups(mgs);
                p.setDataSet(temp);
            }
        }
        return p;
    }
}
