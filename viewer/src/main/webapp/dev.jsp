<!--
Copyright 2014 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author Gagarine Yaikhom <g.yaikhom@har.mrc.ac.uk>
-->

<%@page contentType="text/html" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
    <head>
        <title>PhenoDCC Image Display Web Application</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta http-equiv="X-UA-Compatible" content="chrome=1" />
        <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,600|Roboto:400,100,300,700' rel='stylesheet' type='text/css'>
        <link rel="stylesheet" type="text/css" href="css/imageviewer.css">
    </head>
    <body>
        <div id="image-viewer" style="width: 100%; height: 100%"></div>

        <!--[if lt IE 9]>
        <script>
            window.location = "unsupported.jsp";
        </script>
        <![endif]-->

        <script>
            /* this is the global variable where
             * we expose the public interfaces */
            if (typeof dcc === 'undefined')
                dcc = {};

            var req = new XMLHttpRequest();
            req.open('GET', '../roles', false);
            req.setRequestHeader("Accept", "application/json");
            req.setRequestHeader("Content-Type", "application/json; charset=utf-8");
            req.send(null);
            dcc.roles = JSON.parse(req.responseText);
        </script>

        <script type="text/javascript" src="js/d3.v3.min.js"></script>
        <script type="text/javascript" src="js/imageviewer.js"></script>

        <script>
            window.addEventListener('load', function() {
                var comparative = new dcc.ComparativeImageViewer('image-viewer',
                    {
                        splitType: 'horizontal'
                    });
                comparative.view(
                    <%= request.getParameter("cid")%>,
                    <%= request.getParameter("gid")%>,
                    <%= request.getParameter("sid")%>,
                    '<%= request.getParameter("qeid")%>',
                    <%= request.getParameter("pid")%>,
                    <%= request.getParameter("lid")%>);
            });
        </script>
    </body>
</html>
