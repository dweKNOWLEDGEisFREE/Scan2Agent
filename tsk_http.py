#!/usr/bin/python3.5
# encoding: utf-8
''' tsk_http -- webserver for receiving OCS Agent Data

    tsk_http acts as web server for uploading zlib stream compressed files.

    It defines classes_and_methods

    @author:    EJS
    @copyright: 2018 TBD. All rights reserved.
    @license:   TBD
    @contact:   TBD
    @deffield   
'''


''' Imports
'''
import os, sys, datetime, zlib

from twisted.internet import reactor
from twisted.python   import log
from twisted.web      import resource, server


''' Configuration
'''
# Path settings
path_INBOX = './inbox' 

# Infile Name Creation
inFILE_cntr = 1
inFILE_name = ""

#File Ext
ext_TMP = "tmp"
ext_DAT = "dat"


''' BootUp Preparations
'''
def bootup():
    # Creating Subdirectories
    try:
        if not os.path.exists(path_INBOX):
            os.makedirs(path_INBOX)
    except:
        print ("ERROR: Creating directory "+path_INBOX+" failed")
        return -1
    # BootUp ready
    return 0


''' XML render_POST Data
'''
dat__render_POST = """<?xml version='1.0' encoding='UTF-8'?>
<REPLY>
  <OPTION>
    <NAME>DOWNLOAD</NAME>
    <PARAM EXECUTION_TIMEOUT="120" TIMEOUT="30" PERIOD_LATENCY="1" ON="1" FRAG_LATENCY="10" PERIOD_LENGTH="10" TYPE="CONF" CYCLE_LATENCY="60" />
  </OPTION>
  <INVENTORY_ON_STARTUP>1</INVENTORY_ON_STARTUP>
  <RESPONSE>SEND</RESPONSE>
  <PROLOG_FREQ>24</PROLOG_FREQ>
</REPLY>
""".encode('utf-8')

''' HTML render_GET Data
'''
dat__render_GET_UPLOAD ="""
<html>
    <body>
        Manual OCS iTop Integrator Data Upload <br>
        <form enctype="multipart/form-data" action="/?q=1" method="post">
            <input name="ocs">
            <input type="file" name="data">
            <input type="submit">
        </form>
    </body>
</html>
""".encode('utf-8')

''' HTML render_GET Data
'''
dat__render_GET ="""
<html>
    <body>
        <b>Scan2Agent</b> MAILBOX running ...
    </body>
</html>
""".encode('utf-8')
    

''' Web Server
'''
class Resource(resource.Resource):
    isLeaf = True

    # Manual Upload Section
    def render_GET(self, request):
        print ('GET')
        request.setHeader("Content-Type", "text/html; charset=utf-8")
        return dat__render_GET

    # Upload And Decoding Section 
    def render_POST(self, request):
        # Global
        global inFILE_cntr, inFILE_name
        # Access headers
        self.headers = request.getAllHeaders()
        # Debug Output
        print ('POST')
        print(self.headers)
        print(self.headers[b'content-type'])
        print(self.headers[b'content-length'])
        # Creating Log File Name TIMESTAMP
        tst='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
        if (inFILE_name != tst):
            inFILE_cntr = 1
            inFILE_name = tst
        else:
            inFILE_cntr = inFILE_cntr + 1
        # Saving data
        name=inFILE_name+"-"+str(inFILE_cntr)
        print("saving ... "+name)
        with open(os.path.join(path_INBOX, name+"."+ext_TMP), "wb") as f:
            f.write(request.content.getvalue())
        # atomic file rename for Linux not Windows OS
        os.rename(os.path.join(path_INBOX, name+"."+ext_TMP),
                  os.path.join(path_INBOX, name+"."+ext_DAT))
        # Prepare response
        zData=zlib.compress(dat__render_POST, -1)
        # Ready 
        request.setHeader("Content-Type", "application/x-compressed")
        return zData


''' Server Startup
'''
if __name__ == '__main__':
    # Logfile active
    log.startLogging(sys.stdout)
    # Program Info
    print('tsk_http: Scan2Agent - MAILBOX ...')
    # SHOW PATH
    print('tsk_http: Path - ',sys.argv[0])
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    print ("tsk_http: running from - ", dirname)
    os.chdir(dirname)
    # SHOW USER ID
    print('tsk_http: Real UserID - %d' % os.getuid())
    print('tsk_http: Effective UserID - %d' % os.geteuid())
    # Bootup Preparations
    err=bootup()
    if err != 0:
        exit(err)
    # Server Bootup
    try:
        reactor.listenTCP(80, server.Site(Resource()))
        reactor.run()
    except:
        print("ERROR using port 80 for inbox service.")
    # Exit Code
    exit (-1)
