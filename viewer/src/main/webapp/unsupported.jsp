<!--
Copyright 2013 Medical Research Council Harwell.

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
        <style>
            html, body {
                width: 100%;
                height: 100%;
                background: #fff;
            }

            img {
                border: 0px;
            }
            
            #unsupported-ie {
                font-size: 16px;
                font-family: Arial,Helvetica,sans-serif;
                position:absolute;
                color: #555;
                width: 620px;
                margin-top: -370px;
                margin-left: -330px;
                padding: 30px;
                padding-top: 20px;
                top: 50%;
                left: 50%;
                border: 1px solid #bbb;
            }

            #unsupported-ie p {
                clear: left;
                text-align: center;
            }

            #unsupported-ie ul {
                width: 500px;
                margin-left: auto;
                margin-right: auto;
            }

            #unsupported-ie ul li {
                float: left;
                display: block;
                margin: 10px;
                margin-top: 20px;
                margin-bottom: 40px;
            }
        </style>
    </head>
    <body>
        <div id="unsupported-ie">
            <p><img src="images/logo.png" alt="Google Chrome"></img></p>
            <p>You are using Internet Explorer 8, or older, and it is not supported.</p>
            <p>Please use one of the modern browsers:</p>
            <p>
            <ul>
                <li><a href="http://www.google.com/chrome"><img src="images/chrome_text.png" alt="Google Chrome"></img></a></li>
                <li><a href="http://www.mozilla.org/"><img src="images/firefox_text.png" alt="Mozilla Firefox"></img></a></li>
                <li><a href="http://ie.microsoft.com/"><img src="images/ie_text.png" alt="Microsoft IE 9"></img></a></li>
                <li><a href="http://www.apple.com/safari/"><img src="images/safari_text.png" alt="Apple Safari"></img></a></li>
            </ul>
        </p>
        <br/>

        <p>We apologise for any inconvenience this must have caused.</p>
    </div>
</body>
</html>
