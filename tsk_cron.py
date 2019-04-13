#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' tsk_cron - Scan2Agent collector cronjob
             * Query data from vSphere servers.
             * CleanUp old log files.


    This program is part of the Scan2 Suite.
    https://github.com/dweKNOWLEDGEisFREE

    This program is licensed under the GNU General Public License v3.0

    Copyright 2019 by David Weyand, Ernst Schmid

'''

# IMPORTS
import sys, os, json, requests, datetime, mysql.connector
import lib_logs
from alembic.util.messaging import status
#from pid import PidFile

# VERSION
__all__     = []
__version__ = 0.4
__date__    = '2018-06-01'
__updated__ = '2018-07-26'

# CONFIGURATION DATA
prg_file = None
cfg_file = 'config.json'
log_file = 'cron_log.json'
inf_file = 'cron_inf.json'

# PATH SETTINGS
path_PRG     = None
path_XML     = './data/logfiles'
path_HTML    = './static/data/logfiles'
path_INBOX   = './inbox'
path_ARCHIVE = './archive'



''' GO
'''
if __name__ == "__main__":
    # PROGRAM DATA
    path_PRG, prg_file = os.path.split(os.path.abspath(sys.argv[0]))
    os.chdir(path_PRG)
    print("tsk_cron: prog - "+prg_file)
    print("tsk_cron: path - "+path_PRG)
    # SHOW PARAMETERS
    print('tsk_cron: para - No:'+str(len(sys.argv))+' Str:'+str(sys.argv))
    # SHOW USER ID
    print('tsk_cron: rUID - %d' % os.getuid())
    print('tsk_cron: eUID - %d' % os.geteuid())
    
    # READ CONFIG
    try:
        with open(cfg_file) as json_file:
            data=json.load(json_file)
    except:
        exit(1)
   
    # SAVE CONFIG DATA
    cfg_crontab =data['Crontab'][0]
    cfg_logfile =data['LogFile'][0]
                
    # CHECKING CONFIG - CRONTAB ACTION FLAGS
    if cfg_crontab ==None:
        exit(30)
    if cfg_crontab['doQuery' ]==None:
        exit(31)
    if cfg_crontab['doClean' ]==None:
        exit(32)
    # CHECKING CONFIG - LOGFILES
    if cfg_logfile['number']==None or int(cfg_logfile['number'])==0:
        exit(50)
    if cfg_logfile['age'   ]==None or int(cfg_logfile['age'   ])==0:
        exit(51)

    # TIMESTAMP
    tst='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
    print('tsk_cron: START TIME STAMP ',tst) 
    # UPDATE status
    json_inf={"tst_st":tst, "tst_sp":'', "status":'RUNNING'}
    with open(inf_file, 'w') as outfile:
        json.dump(json_inf, outfile)

    if len(sys.argv)==1 and cfg_crontab['doQuery']==True:
        # Info
        print('tsk_cron: Start background process.', file=sys.stdout)
        # Starting bacground process
        # BUILD UPDATE COMMAND
        cmd=('./tsk_itop.py')
        sys.stdout.flush()
        sys.stderr.flush()
        os.system(cmd)
        # Info
        print('tsk_cron: Stop background process.', file=sys.stdout)
        
    if len(sys.argv)==1 and cfg_crontab['doClean']==True:
        # Info
        print('tsk_cron: Removing outdated log files.', file=sys.stdout)
        # Get current time and date.
        now=datetime.datetime.today()
        # CleanUp of HTML/XML Log File Directory
    #   lib_logs.delOldLogFiles(now, path_HTML, 'html', cfg_logfile['number'], cfg_logfile['age'])
    #   lib_logs.delOldLogFiles(now, path_XML,  'xml',  cfg_logfile['number'], cfg_logfile['age'])
        # CleanUp old files
        lib_logs.delOldFiles(path_XML,     None, cfg_logfile['number'], cfg_logfile['age'])
        lib_logs.delOldFiles(path_HTML,    None, cfg_logfile['number'], cfg_logfile['age'])
        lib_logs.delOldFiles(path_INBOX,   None, cfg_logfile['number'], cfg_logfile['age'])
        lib_logs.delOldFiles(path_ARCHIVE, None, cfg_logfile['number'], cfg_logfile['age'])

    if len(sys.argv)>1:
        # Info
        print('tsk_cron: Start background process.', file=sys.stdout)
        # Starting bacground process
        # BUILD UPDATE COMMAND
        cmd=('./tsk_itop.py')
        sys.stdout.flush()
        sys.stderr.flush()
        os.system(cmd)
        # Info
        print('tsk_cron: Stop background process.', file=sys.stdout)

    # TIMESTAMP
    tnd='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
    print('tsk_cron: STOP TIME STAMP ',tnd) 
    # UPDATE status
    json_inf={"tst_st":tst, "tst_sp":tnd, "status":'STAND BY'}
    with open(inf_file, 'w') as outfile:
        json.dump(json_inf, outfile)
    
    # UPDATE TIME MARKER
    json_log={}
    json_log['cur']=[]
    json_log['cur'].append(tst+' [UID:'+str(os.getuid()).__str__()+'/EUID:'+str(os.geteuid())+']')
    json_log['lst']=[]
    try:
        with open(log_file) as json_file:
            data=json.load(json_file)
            json_log['lst'].append(data['cur'][0])
    except:
        json_log['lst'].append("")
    with open(log_file, 'w') as outfile:
        json.dump(json_log, outfile)

    # READY
    exit(0)
