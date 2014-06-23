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

import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.TypedQuery;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
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

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    @Path("{cid}/{gid}/{sid}/{pid}/{qid}")
    public MediaFileDetailsPack extjsFindBy(
            @PathParam("cid") Integer centreId,
            @PathParam("gid") Integer genotypeId,
            @PathParam("sid") Integer strainId,
            @PathParam("pid") Integer procedureId,
            @PathParam("qid") Integer parameterId,
            @QueryParam("lid") Integer pipelineId,
            @QueryParam("includeBaseline") Boolean includeBaseline) {
        MediaFileDetailsPack p = new MediaFileDetailsPack();
        if (centreId == null || genotypeId == null || strainId == null
                || procedureId == null || parameterId == null) {
            p.setDataSet(null, 0L);
        } else {
            EntityManager em = getEntityManager();
            TypedQuery<MediaFileDetail> query
                    = em.createNamedQuery(pipelineId == null
                            ? "MediaFile.findIgnorePipeline" : "MediaFile.find",
                            MediaFileDetail.class);
            query.setParameter("cid", centreId);
            query.setParameter("gid", genotypeId);
            query.setParameter("sid", strainId);
            query.setParameter("pid", procedureId);
            query.setParameter("qid", parameterId);
            if (pipelineId != null) {
                query.setParameter("lid", pipelineId);
            }
            p.setDataSet(query.getResultList());
            em.close();
        }
        return p;
    }
}
