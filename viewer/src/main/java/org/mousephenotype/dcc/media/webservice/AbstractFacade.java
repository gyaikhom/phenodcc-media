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

import java.util.List;
import javax.persistence.EntityManager;
import javax.persistence.EntityManagerFactory;
import javax.persistence.TypedQuery;
import javax.persistence.criteria.CriteriaQuery;
import javax.persistence.criteria.Root;
import javax.servlet.ServletContext;
import javax.ws.rs.core.Context;
import org.mousephenotype.dcc.media.persistence.PersistenceManager;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 * @param <T>
 */
public abstract class AbstractFacade<T> {

    @Context
    private ServletContext context;
    private final Class<T> entityClass;

    public AbstractFacade(Class<T> entityClass) {
        this.entityClass = entityClass;
    }

    protected EntityManager getEntityManager() {
        PersistenceManager pm =
                (PersistenceManager) context.getAttribute("PersistenceManager");
        EntityManagerFactory emf = pm.getEntityManagerFactory();
        emf.getCache().evictAll();
        return emf.createEntityManager();
    }

    public void create(T entity) {
        EntityManager em = getEntityManager();
        em.getTransaction().begin();
        em.persist(entity);
        em.getTransaction().commit();
        em.refresh(entity);
        em.close();
    }

    public void edit(T entity) {
        EntityManager em = getEntityManager();
        em.getTransaction().begin();
        em.merge(entity);
        em.getTransaction().commit();
        em.refresh(entity);
        em.close();
    }

    public void remove(T entity) {
        EntityManager em = getEntityManager();
        em.getTransaction().begin();
        em.merge(entity);
        em.flush();
        em.refresh(entity);
        em.remove(entity);
        em.getTransaction().commit();
        em.close();
    }

    public T find(Object id) {
        EntityManager em = getEntityManager();
        T returnValue = em.find(entityClass, id);
        em.close();
        return returnValue;
    }

    public List<T> findAll() {
        EntityManager em = getEntityManager();
        CriteriaQuery<T> cq = em.getCriteriaBuilder().createQuery(entityClass);
        cq.select(cq.from(entityClass));
        List<T> returnValue = em.createQuery(cq).getResultList();
        em.close();
        return returnValue;
    }

    public List<T> findRange(int[] range) {
        EntityManager em = getEntityManager();
        CriteriaQuery<T> cq = em.getCriteriaBuilder().createQuery(entityClass);
        cq.select(cq.from(entityClass));
        TypedQuery<T> q = getEntityManager().createQuery(cq);
        q.setMaxResults(range[1] - range[0]);
        q.setFirstResult(range[0]);
        List<T> returnValue = q.getResultList();
        em.close();
        return returnValue;
    }

    public Long count() {
        EntityManager em = getEntityManager();
        CriteriaQuery<Long> cq = em.getCriteriaBuilder().createQuery(Long.class);
        Root<T> rt = cq.from(entityClass);
        cq.select(getEntityManager().getCriteriaBuilder().count(rt));
        TypedQuery<Long> q = getEntityManager().createQuery(cq);
        Long returnValue = q.getSingleResult();
        em.close();
        return returnValue;
    }

}
