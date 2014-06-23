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
package org.mousephenotype.dcc.media.persistence;

import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

/**
 *
 * @author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
 */
public class PersistenceListener implements ServletContextListener {

    @Override
    public void contextInitialized(ServletContextEvent event) {
        ServletContext ctx = event.getServletContext();
        PersistenceManager pm =
                (PersistenceManager) ctx.getAttribute("PersistenceManager");
        if (pm == null) {
            ctx.setAttribute("PersistenceManager", new PersistenceManager());
        }
    }

    @Override
    public void contextDestroyed(ServletContextEvent event) {
        ServletContext ctx = event.getServletContext();
        PersistenceManager pm =
                (PersistenceManager) ctx.getAttribute("PersistenceManager");
        pm.closeEntityManagerFactory();
        ctx.removeAttribute("PersistenceManager");
    }
}
