#!/usr/bin/python3.5
# encoding: utf-8
''' tsk_itop -- processing OCS Agent Data

    tsk_itop will: * check the INBOX directory for compressed OCS Agent files.
                   * unzip the OCS Agent Data Files.
                   * analyzing the unziped XML file.
                   * creating a CVS file out of the XML data file.
                   * calling the PHP iTop transfer program.

    It defines classes_and_methods

    @author:    EJS
    @copyright: 2018 TBD. All rights reserved.
    @license:   TBD
    @contact:   TBD
    @deffield   
'''

# Database Structure
'''
CREATE DATABASE `scan2Agent_01` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;

USE `scan2Agent_01`;

CREATE TABLE `iTop_IPv4Address` (
  `ip` varchar(20) NOT NULL,
  `org_id` int(11) NOT NULL DEFAULT '0',
  `IPv4Address_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_IPv4Range` (
  `org_id` int(11) NOT NULL DEFAULT '0',
  `org_name` varchar(255) DEFAULT '',
  `firstip` int(10) unsigned NOT NULL,
  `lastip` int(10) unsigned NOT NULL,
  `firstip_t` varchar(20) NOT NULL,
  `lastip_t` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_LogicalInterface` (
  `name` varchar(255) NOT NULL,
  `comment` text,
  `speed` decimal(12,2) DEFAULT NULL,
  `ip_list` text,
  `macaddress` varchar(255) DEFAULT NULL,
  `virtualmachine_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_OSLicence` (
  `name` varchar(128) NOT NULL,
  `org_id` int(11) NOT NULL DEFAULT '0',
  `description` text,
  `licence_key` varchar(128) DEFAULT NULL,
  `osversion_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`name`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_OtherSoftware` (
  `name` varchar(128) NOT NULL,
  `org_id` int(11) NOT NULL DEFAULT '0',
  `system_id` varchar(255) DEFAULT NULL,
  `software_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`name`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_Software` (
  `name` varchar(128) NOT NULL,
  `vendor` varchar(128) NOT NULL,
  `version` varchar(128) NOT NULL,
  `type` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`name`,`vendor`,`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `iTop_VirtualMachine` (
  `name` varchar(128) NOT NULL,
  `org_id` int(11) NOT NULL DEFAULT '0',
  `cpu` int(11) DEFAULT NULL,
  `ram` int(11) DEFAULT NULL,
  `osfamily_id` int(11) DEFAULT NULL,
  `osversion_id` int(11) DEFAULT NULL,
  `oslicence_id` int(11) DEFAULT NULL,
  `virtualhost_id` int(11) DEFAULT NULL,
  `status` varchar(128) DEFAULT NULL,
  `description` text,
  `managementip_id` int(11) DEFAULT NULL,
  `business_criticity` varchar(128) DEFAULT NULL,
  `documents_list` text,
  `contacts_list` text,
  `tickets_list` text,
  `providercontracts_list` text,
  `logicalvolumes_list` text,
  `applicationsolution_list` text,
  `move2production` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`name`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LkTb_Software` (
  `name` varchar(255) NOT NULL,
  `vendor` varchar(255) DEFAULT NULL,
  `version` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LkTb_VirtualMachine` (
  `name` varchar(128) NOT NULL,
  `org_id` int(11) NOT NULL,
  `virtualhost_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

# Database Commands
'''
CREATE USER 'OCSadmin'@'localhost' IDENTIFIED BY '@OCSadmin#2017';
GRANT ALL PRIVILEGES ON *.* TO 'OCSadmin'@'localhost';
FLUSH PRIVILEGES;

USE scan2Agent_01;
DELETE FROM iTop_IPv4Address;
DELETE FROM iTop_IPv4Range;
DELETE FROM iTop_LogicalInterface;
DELETE FROM iTop_OSLicence;
DELETE FROM iTop_OtherSoftware;
DELETE FROM iTop_Software;
DELETE FROM iTop_VirtualMachine;
'''

''' Imports
'''
import os, sys, datetime, zlib, xml.sax
import json, requests
import ipaddress
import mysql.connector
#import datetime, tempfile


''' Configuration
'''
# File settings
cfg_file = 'config.json'

# iTop ACCESS DATA- Language Settings to EN US
cfg_itop_cr = {
    'url' : 'http://172.16.0.201',
    'usr' : 'syncUsrOCS',
    'pwd' : 'syncPwdOCS'
}

# mySQL ACCESS DATA
cfg_mysql_cr = {
    'host'    : 'localhost',
    'database': 'ocs4iTopDB',
    'user'    : 'OCSadmin',
    'password': '@OCSadmin#2017'
}

# Path settings
path_INBOX = './inbox' 
path_ARCHV = './archive' 

#File Ext
ext_DAT = "dat"
ext_OCS = "ocs"
ext_ERR = "err"
ext_XML = "xml"

# DEFAULT ASSIGNMENTS
DEFAULT_ORG_ID         = 0
DEFAULT_VIRTUALHOST_ID = "0"


''' Processing config file
'''
def readConfigFile():
    # External
    global cfg_itop_cr, cfg_mysql_cr
    # READ CONFIG
    try:
        with open(cfg_file) as json_file:
            data=json.load(json_file)
    except:
        return False
    # SAVE CONFIG DATA
    cfg_itop_cr =data['iTop' ][0]
    cfg_mysql_cr=data['mySQL'][0]
    # CHECKING CONFIG - iTop PARAMETERS
    if cfg_itop_cr  == None:
        return False
    if cfg_mysql_cr == None:
        return False
    # Ready
    return True


''' iTop: Requesting all currently IP addresses in use from iTop.
'''
def iTopQuery_IpAddress():
    # REST
    try:
        # REST REQUEST CREATE
        json_data = {
            'operation': 'core/get',
            'class'    : 'IPv4Address',
            'key'      : "SELECT IPAddress"
        }
        encoded_data = json.dumps(json_data)
        # REST REQUEST TRANSMITT
        res = requests.post(cfg_itop_cr.get('url')+'/webservices/rest.php?version=1.0',
                            verify=False,
                            data={'auth_user': cfg_itop_cr.get('usr'), 
                                  'auth_pwd' : cfg_itop_cr.get('pwd'),
                                  'json_data': encoded_data})
    except:
        print('ERROR...: iTop REST ACCESS FAILED IPv4Address', file=sys.stderr)
        return False    
    # DATABASE TRANSFER
    result = json.loads(res.text);
    if result['code']==0 and result['objects']!=None:        
        # Transfer data into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect iTop_IPv4Address')
            cnx = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # delete old entries
            print('tsk_iTop: SQL delete')
            cmd=("""DELETE FROM iTop_IPv4Address""")
            cursor.execute(cmd)
            # write data
            print('tsk_iTop: SQL insert')
            for i in result['objects'].keys():
                if len(result['objects'][i]['fields']['ip'])==0:
                    continue
                cmd=("""INSERT INTO iTop_IPv4Address(ip,org_id,IPv4Address_id) VALUES (%s,%s,%s)""")
                cursor.execute(cmd, (result['objects'][i]['fields']['ip'],
                                     result['objects'][i]['fields']['org_id'],
                                     int(i.replace('IPv4Address::', ''))))
            # close connection
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()
        return True
    # No data
    return True
#   return False


''' iTop: Requesting all currently IP ranges in use from iTop.
'''
def iTopQuery_IpRange():
    # REST
    try:
        # REST REQUEST CREATE
        json_data = {
            'operation': 'core/get',
            'class'    : 'IPv4Range',
            'key'      : "SELECT IPv4Range"
        }
        encoded_data = json.dumps(json_data)
        # REST REQUEST TRANSMITT
        res = requests.post(cfg_itop_cr.get('url')+'/webservices/rest.php?version=1.0',
                            verify=False,
                            data={'auth_user': cfg_itop_cr.get('usr'), 
                                  'auth_pwd' : cfg_itop_cr.get('pwd'),
                                  'json_data': encoded_data})
    except:
        print('ERROR...: iTop REST ACCESS FAILED IPv4Range', file=sys.stderr)
        return False    
    # DATABASE TRANSFER
    result = json.loads(res.text);
    if result['code']==0 and result['objects']!=None:        
        # Transfer data into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect iTop_IPv4Range')
            cnx = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # delete old entries
            print('tsk_iTop: SQL delete')
            cmd=("""DELETE FROM iTop_IPv4Range""")
            cursor.execute(cmd)
            # write data
            print('tsk_iTop: SQL insert')
            for i in result['objects'].keys():
                cmd=("""INSERT INTO iTop_IPv4Range(firstip,lastip,org_id,org_name,firstip_t,lastip_t) VALUES (%s,%s,%s,%s,%s,%s)""")
                cursor.execute(cmd, (int(ipaddress.IPv4Address(result['objects'][i]['fields']['firstip'])),
                                     int(ipaddress.IPv4Address(result['objects'][i]['fields']['lastip' ])), 
                                     result['objects'][i]['fields']['org_id'], 
                                     result['objects'][i]['fields']['org_name'],
                                     result['objects'][i]['fields']['firstip'],
                                     result['objects'][i]['fields']['lastip' ]))
            # close connection                    
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()
        return True
    # No data
    return True
#   return False


''' iTop: Requesting all VirtualMachine to get the virtualhost_id from iTop.
'''
def iTopQuery_VirtualMachine():
    # REST
    try:
        # REST REQUEST CREATE
        json_data = {
            'operation': 'core/get',
            'class'    : 'VirtualMachine',
            'key'      : "SELECT VirtualMachine"
        }
        encoded_data = json.dumps(json_data)
        # REST REQUEST TRANSMITT
        res = requests.post(cfg_itop_cr.get('url')+'/webservices/rest.php?version=1.0',
                            verify=False,
                            data={'auth_user': cfg_itop_cr.get('usr'), 
                                  'auth_pwd' : cfg_itop_cr.get('pwd'),
                                  'json_data': encoded_data})
    except:
        print('ERROR...: iTop REST ACCESS FAILED VirtualMachine', file=sys.stderr)
        return False    
    # DATABASE TRANSFER
    result = json.loads(res.text);
    if result['code']==0 and result['objects']!=None:
        # Transfer data into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect LkTb_VirtualMachine')
            cnx = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # delete old entries
            print('tsk_iTop: SQL delete')
            cmd=("""DELETE FROM LkTb_VirtualMachine""")
            cursor.execute(cmd)
            # write data
            print('tsk_iTop: SQL insert')
            for i in result['objects'].keys():
                cmd=("""INSERT INTO LkTb_VirtualMachine(name,org_id,virtualhost_id) VALUES (%s,%s,%s)""")
                cursor.execute(cmd, (result['objects'][i]['fields']['name'], 
                                     result['objects'][i]['fields']['org_id'], 
                                     result['objects'][i]['fields']['virtualhost_id']))
            # close connection                    
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()
        return True
    # No data
    return True
#   return False


''' iTop: Requesting all Software from iTop.
'''
def iTopQuery_Software():
    # REST
    try:
        # REST REQUEST CREATE
        json_data = {
            'operation': 'core/get',
            'class'    : 'Software',
            'key'      : "SELECT Software"
        }
        encoded_data = json.dumps(json_data)
        # REST REQUEST TRANSMITT
        res = requests.post(cfg_itop_cr.get('url')+'/webservices/rest.php?version=1.0',
                            verify=False,
                            data={'auth_user': cfg_itop_cr.get('usr'), 
                                  'auth_pwd' : cfg_itop_cr.get('pwd'),
                                  'json_data': encoded_data})
    except:
        print('ERROR...: iTop REST ACCESS FAILED Software', file=sys.stderr)
        return False
    # DATABASE TRANSFER
    result = json.loads(res.text);
    if result['code']==0 and result['objects']!=None:
#       print (result)
        # DEBUG OUTPUT
#       for i in result['objects'].keys():
#           print(i)
#           print(result['objects'][i]['fields']['name'],
#                 result['objects'][i]['fields']['vendor'],
#                 result['objects'][i]['fields']['version'],
#                 result['objects'][i]['fields']['type'])
        # Transfer data into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect LkTb_Software')
            cnx = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # delete old entries
            print('tsk_iTop: SQL delete')
            cmd=("""DELETE FROM LkTb_Software""")
            cursor.execute(cmd)
            # write data
            print('tsk_iTop: SQL insert')
            for i in result['objects'].keys():
                cmd=("""INSERT INTO LkTb_Software(name,vendor,version,type) VALUES (%s,%s,%s,%s)""")
                cursor.execute(cmd, (result['objects'][i]['fields']['name'],
                                     result['objects'][i]['fields']['vendor'],
                                     result['objects'][i]['fields']['version'],
                                     result['objects'][i]['fields']['type']))
            # close connection                    
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()
        return True
    # No data
    return True
#   return False


''' mySQL: Search for the corresponding IPv4Address ID.
***        Name:ip  Type:String
'''
def getDB_IPv4Address_ID(ip, org_id):
    # Search SQL-DB for IPv4Address ID
    try:
        # open connection
        print('tsk_iTop: SQL connect - search ip org_id')
        cnx = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # search data
        if org_id == None:
            print('tsk_iTop: SQL select ip['+ip+']')
            cmd=("SELECT IPv4Address_id,ip,org_id FROM iTop_IPv4Address WHERE %s=ip ORDER BY org_id LIMIT 0,1")
            cursor.execute(cmd, (ip,))
        #   print(cursor.statement)
        else:
            print('tsk_iTop: SQL select ip['+ip+'] org_id['+str(org_id)+']')
            cmd=("SELECT IPv4Address_id,ip,org_id FROM iTop_IPv4Address WHERE %s=ip AND %s=org_id ORDER BY org_id LIMIT 0,1")
            cursor.execute(cmd, (ip, org_id))
        #   print(cursor.statement)
        # retrieve data
        res=cursor.fetchone()
        # print(res)
        if res!=None:
            print('tsk_iTop: SQL result IPv4Address_id['+str(res[0])+'] ip['+str(res[1])+'] org_id['+str(res[2])+']')
        #   print('tsk_iTop: SQL result IPv4Address_id['+str(res[0])+']')
            res=res[0]
        # close connection
        cursor.close()
    except mysql.connector.Error as err:
        res=None
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
    else:
        print('tsk_iTop: SQL close')
        cnx.close()
    return res


''' mySQL: Search for the corresponding ORG_ID.
***        Name:ipADDR  Type:ipaddress
'''
def getDB_ORG_ID__IP(ipADDR):
    # Nothing
    if ipADDR==None or len(ipADDR)==0:
        return None
    # Search SQL-DB for ipADDR
    try:
        # open connection
        print('tsk_iTop: SQL connect - search ipADDR')
        cnx = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # search data
        print('tsk_iTop: SQL select ipADDR['+str(ipADDR)+']')
        cmd=("SELECT org_id,org_name FROM iTop_IPv4Range WHERE %s>=firstip AND %s<=lastip LIMIT 0,1")
    #   cmd=("SELECT org_id FROM iTop_IPv4Range WHERE %s>=firstip AND %s<=lastip LIMIT 0,1")
        cursor.execute(cmd, (int(ipaddress.IPv4Address(ipADDR)),
                             int(ipaddress.IPv4Address(ipADDR))))
        #   print(cursor.statement)
        # retrieve data
        res=cursor.fetchone()
        if res!=None:
            print('tsk_iTop: SQL result org_id['+str(res[0])+'] org_name['+res[1]+']')
        #   print('tsk_iTop: SQL result org id['+str(res[0])+']')
            res=res[0]
        # close connection
        cursor.close()
    except mysql.connector.Error as err:
        res=None
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
    else:
        print('tsk_iTop: SQL close')
        cnx.close()
    return res


''' mySQL: Search for the corresponding ORG_ID.
***        Name:hName  Type:String
'''
def getDB_ORG_ID__HOST(hName):
    # Search SQL-DB for hName
    try:
        # open connection
        print('tsk_iTop: SQL connect - search HOST NAME')
        cnx = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # search data
        print('tsk_iTop: SQL select HOST NAME['+str(hName)+']')
        cmd=("SELECT name,org_id,virtualhost_id FROM LkTb_VirtualMachine WHERE name LIKE %s ORDER BY name,org_id,virtualhost_id LIMIT 0,1")
        cursor.execute(cmd, (str(hName),))
        # print(cursor.statement)
        # retrieve data
        res=cursor.fetchone()
        if res!=None:
            res=res[1]
            print('tsk_iTop: SQL result org_id['+str(res)+']')
        # close connection
        cursor.close()
    except mysql.connector.Error as err:
        res=None
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
    else:
        print('tsk_iTop: SQL close')
        cnx.close()
    return res


''' mySQL: Search for the corresponding virtualhost_id.
***        Name:vmNAME  Type:VirtualMachine Name
'''
def getDB_VIRTUALHOST_ID(vmNAME):
    # Search SQL-DB for name
    try:
        # open connection
        print('tsk_iTop: SQL connect - search VirtualHost ID')
        cnx = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # search data
        print('tsk_iTop: SQL select VirtualMachine Name['+str(vmNAME)+']')
        cmd=("SELECT name,org_id,virtualhost_id FROM LkTb_VirtualMachine WHERE name LIKE %s ORDER BY name,org_id,virtualhost_id LIMIT 0,1")
        cursor.execute(cmd, (str(vmNAME),))
        #   print(cursor.statement)
        # retrieve data
        res=cursor.fetchone()
        if res!=None:
            print('tsk_iTop: SQL result name['+str(res[0])+'] org_id['+str(res[1])+'] virtualhost_id['+str(res[2])+']')
            res=res[2]
        # close connection
        cursor.close()
    except mysql.connector.Error as err:
        res=None
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
    else:
        print('tsk_iTop: SQL close')
        cnx.close()
    return res


''' mySQL: Insert the LOGICAL INTERFACE
***        Parameter: name 
***                 : comment
***                 : speed
***                 : ip_list 
***                 : macaddress
***                 : virtualmachine_id
'''
def putDB_LOGICAL_INTERFACE(name, comment, speed, ip_list, 
                            macaddress, virtualmachine_id):
    # Check preconditions
    if name==None or len(name)==0:
        return
    if virtualmachine_id==None or len(virtualmachine_id)==0:
        return
    
    # CREATE PRESETS
    vn_name              = name
    vn_comment           = comment
    vn_speed             = speed
    vn_ip_list           = ip_list
    vn_macaddress        = macaddress
    vn_virtualmachine_id = virtualmachine_id

    # Inser licence into SQL-DB
    try:
        # open connection
        print('tsk_iTop: SQL connect - insert LOGICAL INTERFACE')
        cnx    = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # count data
        print('tsk_iTop: SQL counting insert/update')
        cmd=("SELECT COUNT(*) FROM iTop_LogicalInterface "
             "WHERE name=%s AND virtualmachine_id=%s")
        cursor.execute(cmd, (vn_name,vn_virtualmachine_id))
        # update/insert
        if cursor.fetchone()[0]==0:
            cmd=("INSERT INTO iTop_LogicalInterface("
                 "name,comment,speed,ip_list,"
                 "macaddress,virtualmachine_id) "
                 "VALUES(%s,%s,%s,%s,%s,%s)")
            cursor.execute(cmd, (vn_name,vn_comment,vn_speed,vn_ip_list,
                                 vn_macaddress,vn_virtualmachine_id))
        else:
            cmd=("UPDATE iTop_LogicalInterface SET "
                 "name=%s,comment=%s,speed=%s,ip_list=%s,"
                 "macaddress=%s,virtualmachine_id=%s "
                 "WHERE name=%s AND virtualmachine_id=%s")
            cursor.execute(cmd, (vn_name,vn_comment,vn_speed,vn_ip_list,
                                 vn_macaddress,vn_virtualmachine_id,
                                 vn_name,vn_virtualmachine_id))
        # close connection
        cursor.close()
        cnx.commit()
    except mysql.connector.Error as err:
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
        if 'cnx' in locals():
            cnx.rollback()
    else:
        print('tsk_iTop: SQL close')
        cnx.close()


''' mySQL: Insert the licence key of the software.
***        Parameter: licencekey  Type:String
***                 : org_id      Type:Integer
'''
def putDB_LICENCE_KEY(prodkey, org_id, prodid, osversion_id):
    # Check preconditions
    if prodkey==None or len(prodkey)==0:
        return
    if prodkey==None or len(prodkey)==0:
        return
    
    # Create default values
    now      = datetime.datetime.today()
    now_date = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M:%S")

    # CREATE PRESETS
    vn_name         = prodkey
    vn_org_id       = org_id
    vn_description  = "Created on "+now_date+" "+now_time
    vn_licence_key  = prodid
    vn_osversion_id = osversion_id
    
    # Inser licence into SQL-DB
    try:
        # open connection
        print('tsk_iTop: SQL connect - insert LICENCE KEY')
        cnx = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # write data
        print('tsk_iTop: SQL insert/update')
        cmd=("INSERT INTO iTop_OSLicence("
             "name,org_id,"
             "description,licence_key,osversion_id) "
             "VALUES(%s,%s,%s,%s,%s) "
             "ON DUPLICATE KEY UPDATE "
             "description=%s,licence_key=%s,osversion_id=%s")
        cursor.execute(cmd, (vn_name,vn_org_id,
                             vn_description,vn_licence_key,vn_osversion_id,
                             vn_description,vn_licence_key,vn_osversion_id))
        # close connection
        cursor.close()
        cnx.commit()
    except mysql.connector.Error as err:
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
        if 'cnx' in locals():
            cnx.rollback()
    else:
        print('tsk_iTop: SQL close')
        cnx.close()



''' Extracting: OCS Data
'''
def toolExtract(name):

    class nMapHandler( xml.sax.ContentHandler ):
        def __init__(self, target):
            self.target=target
            self.tag_levA=None

        def characters(self, info):
            self.tag_data=info
        #   print("["+info+"]")

        def startElement(self, tag, attrs):
            self.tag_data=None
        #   print("->"+tag)
            # HARDWARE
            if tag == "HARDWARE":
                self.tag_levA=tag
                self.tag_nm_NAME      =None
                self.tag_nm_OSNAME    =None
                self.tag_nm_OSVERSION =None
                self.tag_nm_ARCH      =None
                self.tag_nm_PROCESSORT=None
                self.tag_nm_PROCESSORN=None
                self.tag_nm_MEMORY    =None
                self.tag_nm_IPADDR    =None
                self.tag_nm_WINPRODID =None
                self.tag_nm_WINPRODKEY=None
            # CPUS
            if tag == "CPUS":
                self.tag_levA=tag
                self.tag_nm_TYPE =None
                self.tag_nm_CORES=None
            # NETWORKS
            if tag == "NETWORKS":
                self.tag_levA=tag
                self.tag_nm_DESCRIPTION=None
                self.tag_nm_SPEED      =None
                self.tag_nm_MACADDR    =None
                self.tag_nm_IPADDR     =None
            # SOFTWARES
            if tag == "CONTENT":
                self.tag_nn_SOFTWARES=0
            if tag == "SOFTWARES":
                self.tag_levA=tag
                self.tag_nn_SOFTWARES+=1
                self.tag_nm_NAME   =None
                self.tag_nm_VENDOR =None
                self.tag_nm_VERSION=None
                self.tag_nm_TYPE   =None
                
        def endElement(self, tag):
            # BASE ITEMS       
            if tag == "DEVICEID":
                tag_DIR[tag]=self.tag_data
            if tag == "IPADDRESS":
                tag_DIR[tag]=self.tag_data
            # HARDWARE
            if self.tag_levA == "HARDWARE":
                if tag == "NAME":
                    self.tag_nm_NAME=self.tag_data
                if tag == "OSNAME":
                    self.tag_nm_OSNAME=self.tag_data
                if tag == "OSVERSION":
                    self.tag_nm_OSVERSION=self.tag_data
                if tag == "ARCH":
                    self.tag_nm_ARCH=self.tag_data
                if tag == "PROCESSORT":
                    self.tag_nm_PROCESSORT=self.tag_data
                if tag == "PROCESSORN":
                    self.tag_nm_PROCESSORN=self.tag_data
                if tag == "MEMORY":
                    self.tag_nm_MEMORY=self.tag_data
                if tag == "IPADDR":
                    self.tag_nm_IPADDR=self.tag_data
                if tag == "WINPRODID":
                    self.tag_nm_WINPRODID=self.tag_data
                if tag == "WINPRODKEY":
                    self.tag_nm_WINPRODKEY=self.tag_data
            if tag == "HARDWARE":
                self.tag_levA=None
                tag_DIR[tag+':NAME'      ]=self.tag_nm_NAME
                tag_DIR[tag+':OSNAME'    ]=self.tag_nm_OSNAME
                tag_DIR[tag+':OSVERSION' ]=self.tag_nm_OSVERSION
                tag_DIR[tag+':ARCH'      ]=self.tag_nm_ARCH
                tag_DIR[tag+':PROCESSORT']=self.tag_nm_PROCESSORT
                tag_DIR[tag+':PROCESSORN']=self.tag_nm_PROCESSORN
                tag_DIR[tag+':MEMORY'    ]=self.tag_nm_MEMORY
                tag_DIR[tag+':IPADDR'    ]=self.tag_nm_IPADDR
                tag_DIR[tag+':WINPRODID' ]=self.tag_nm_WINPRODID
                tag_DIR[tag+':WINPRODKEY']=self.tag_nm_WINPRODKEY
            # CPUS
            if self.tag_levA == "CPUS":
                if tag == "TYPE":
                    self.tag_nm_TYPE=self.tag_data
                if tag == "CORES":
                    self.tag_nm_CORES=self.tag_data
            if tag == "CPUS":
                self.tag_levA=None
                tag_DIR[tag+':TYPE' ]=self.tag_nm_TYPE
                tag_DIR[tag+':CORES']=self.tag_nm_CORES
            # NETWORKS
            if tag == "NETWORKS":
                self.tag_levA=None
            # SOFTWARES
            if self.tag_levA == "SOFTWARES":
                if tag == "NAME":
                    self.tag_nm_NAME   =self.tag_data
                if tag == "FROM":
                    self.tag_nm_VENDOR =self.tag_data
                if tag == "VERSION":
                    self.tag_nm_VERSION=self.tag_data
                if tag == "TYPE":
                    self.tag_nm_TYPE   =self.tag_data
            if tag == "SOFTWARES":
                self.tag_levA=None
                no='n'+str(self.tag_nn_SOFTWARES)
                tag_DIR[tag+no+':NAME'   ]=self.tag_nm_NAME
                tag_DIR[tag+no+':VENDOR' ]=self.tag_nm_VENDOR
                tag_DIR[tag+no+':VERSION']=self.tag_nm_VERSION
                tag_DIR[tag+no+':TYPE'   ]='PCSoftware' #'1' #'PC Software'
    
    def nMapCoroutine(func):
        def start(*args, **kwargs):
            cr=func(*args, **kwargs)
            next(cr)
            return cr
        return start

    @nMapCoroutine
    def datStore():
        while True:
            event = (yield)
            for dat in event:
                print ("Store: ["+dat+"]")

    ''' scanning XML file '''
    tag_DIR = {}
    print('tsk_itop: XML access')
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    parser.setFeature(xml.sax.handler.feature_validation,False)
    parser.setContentHandler(nMapHandler(datStore()))
    parser.parse(open(name, "r"))
#   print (tag_DIR)
    return tag_DIR


''' Clean: OCS Data CleanUp
'''
def toolCleanUp():
    # Job for ...
    print("tsk_itop: DELETE VirtualMachine Software OtherSoftware")
    # Delete SQL-DB entries
    try:
        # open connection
        print('tsk_iTop: SQL connect - CleanUp')
        cnx    = mysql.connector.connect(**cfg_mysql_cr)
        cursor = cnx.cursor()
        # delete old entries for VirtualMachine
        print('tsk_iTop: SQL delete iTop_VirtualMachine')
        cmd=("""DELETE FROM iTop_VirtualMachine""")
        cursor.execute(cmd)
        # delete old entries for Software
        print('tsk_iTop: SQL delete iTop_Software')
        cmd=("""DELETE FROM iTop_Software""")
        cursor.execute(cmd)
        # delete old entries for OtherSoftware
        print('tsk_iTop: SQL delete iTop_OtherSoftware')
        cmd=("""DELETE FROM iTop_OtherSoftware""")
        cursor.execute(cmd)
        # close connection
        cursor.close()
        cnx.commit()
    except mysql.connector.Error as err:
        print(err, file=sys.stderr)
        if 'cursor' in locals():
            print(cursor.statement, file=sys.stderr)
        if 'cnx' in locals():
            cnx.rollback()
    else:
        print('tsk_iTop: SQL close')
        cnx.close()


''' Update: OCS Data
'''
def toolUpdate(data):

    def process_SOFTWARE():
        # DATABASE TRANSFER
        if not 'SOFTWARESn1:NAME' in data:
            return
        # Job for ...
        print("tsk_itop: INSERT/UPDATE SOFTWARE")
        # Inser into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect - insert SOFTWARE')
            cnx    = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # LOOP
            no=1
            while 'SOFTWARESn'+str(no)+':NAME' in data:
                # Data
                vn_NAME   =data['SOFTWARESn'+str(no)+':NAME'   ]
                vn_VENDOR =data['SOFTWARESn'+str(no)+':VENDOR' ]
                vn_VERSION=data['SOFTWARESn'+str(no)+':VERSION']
                vn_TYPE   =data['SOFTWARESn'+str(no)+':TYPE'   ]
                # Next element
                if vn_NAME==None or len(vn_NAME)==0:
                    no+=1
                    continue;
                if vn_VENDOR==None or len(vn_VENDOR)==0:
                    vn_VENDOR='unknown'
                if vn_VERSION==None or len(vn_VERSION)==0:
                    vn_VERSION='unknown'
                # Insert/Update
                cmd=("INSERT INTO iTop_Software("
                     "name,vendor,version,type) "
                         "VALUES(%s,%s,%s,%s)" 
                         "ON DUPLICATE KEY UPDATE "
                         "type=%s")
                cursor.execute(cmd, (vn_NAME, vn_VENDOR, vn_VERSION, vn_TYPE, vn_TYPE))
                # Next element
                no+=1
            # close connection
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()

    def process_OTHERSOFTWARE():
        # DATABASE TRANSFER
        if not 'SOFTWARESn1:NAME' in data:
            return
        # Job for ...
        print("tsk_itop: INSERT/UPDATE OTHERSOFTWARE")
        # Inser into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect - insert OTHERSOFTWARE')
            cnx    = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # LOOP
            no=1
            while 'SOFTWARESn'+str(no)+':NAME' in data:
                # Data
                # write data
                cmd=("INSERT INTO iTop_OtherSoftware("
                     "name,"
                     "org_id,system_id,software_id) "
                     "VALUES(%s,%s,%s,%s) "
                     "ON DUPLICATE KEY UPDATE "
                     "system_id=%s,software_id=%s")
                cursor.execute(cmd, (data['SOFTWARESn'+str(no)+':NAME'],
                                     org_id,sys_hn,data['SOFTWARESn'+str(no)+':NAME'],
                                     sys_hn,data['SOFTWARESn'+str(no)+':NAME']))
                # Next element
                no+=1
            # close connection
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()

    def process_HARDWARE():
        # Job for ...
        print("tsk_itop: INSERT/UPDATE ["+sys_hn+"]")
        # CREATE PRESETS
        vn_description        = "Created on "+now_date+" "+now_time
        vn_business_criticity = "low"
        vn_move2production    = now_date
        vn_status             = "production"
        vn_cpu                = 0
        vn_ram                = 0
        vn_virtualhost_id     = DEFAULT_VIRTUALHOST_ID
        vn_managementip_id    = None
        # UPDATE PRESETS
        if 'CPUS:CORES' in data:
            vn_cpu=data['CPUS:CORES']
        if 'HARDWARE:MEMORY' in data and data['HARDWARE:MEMORY']!=None:
            vn_ram=str(int(data['HARDWARE:MEMORY'])/1024)
        # MANAGEMENT IP
        if sys_ip!=None:
            vn_managementip_id = getDB_IPv4Address_ID(sys_ip, None)
        # VIRTUALHOST_ID
        tmp=getDB_VIRTUALHOST_ID(sys_hn)
        if tmp!=None:
            vn_virtualhost_id=tmp
        # CREATE PRESETS FOR LogicalInterface TABLE
        # CREATE UPDATE FOR LogicalInterface TABLE
        # CREATE PRESETS FOR OSLicence TABLE
        vn_prodid =None
        vn_prodkey=None
        # UPDATE PRESETS FOR OSLicence TABLE
        if 'HARDWARE:WINPRODID' in data:
            vn_prodid=data['HARDWARE:WINPRODID']
        if 'HARDWARE:WINPRODKEY' in data:
            vn_prodkey=data['HARDWARE:WINPRODKEY']
        if vn_prodkey != None:
            putDB_LICENCE_KEY(vn_prodkey,org_id,vn_prodid,None)
        # Transfer data into SQL-DB
        try:
            # open connection
            print('tsk_iTop: SQL connect')
            cnx = mysql.connector.connect(**cfg_mysql_cr)
            cursor = cnx.cursor()
            # write data
            print('tsk_iTop: SQL insert/update')
            cmd=("INSERT INTO iTop_VirtualMachine("
                 "name,"
                 "description,org_id,business_criticity,"
                 "move2production,status,virtualhost_id,"
                 "cpu,ram,managementip_id) "
            #    "oslicence_id) "
                 "VALUES(%s, %s,%s,%s, %s,%s,%s, %s,%s,%s) "
                 "ON DUPLICATE KEY UPDATE "
                 "org_id=%s,virtualhost_id=%s,"
                 "cpu=%s,ram=%s,managementip_id=%s"
            #    "oslicence_id=%s"
                 )
            cursor.execute(cmd, (sys_hn,
                                 vn_description,org_id,vn_business_criticity,
                                 vn_move2production,vn_status,vn_virtualhost_id,
                                 vn_cpu,vn_ram,vn_managementip_id,
                            #    vn_prodkey,
                                 org_id,vn_virtualhost_id,
                                 vn_cpu,vn_ram,vn_managementip_id,
                            #    vn_prodkey
                                 ))
        #   print(cursor.statement, file=sys.stderr)
            # close connection
            cursor.close()
            cnx.commit()
        except mysql.connector.Error as err:
            print(err, file=sys.stderr)
            if 'cursor' in locals():
                print(cursor.statement, file=sys.stderr)
            if 'cnx' in locals():
                cnx.rollback()
        else:
            print('tsk_iTop: SQL close')
            cnx.close()


    # System Name -> system_id
    if not 'HARDWARE:NAME' in data:
        return None
    sys_hn=data['HARDWARE:NAME']
    # IP Address -> org_id
    if 'HARDWARE:IPADDR' in data:
        sys_ip=data['HARDWARE:IPADDR']
        org_id=getDB_ORG_ID__IP(sys_ip)
    # HOST NAME -> org_id
    if org_id==None:
        sys_ip=None
        org_id=getDB_ORG_ID__HOST(sys_hn)
    # HOST NAME -> org_id
    if org_id==None:
        sys_ip=None
        org_id=DEFAULT_ORG_ID
    # Create date, time
    now      = datetime.datetime.today()
    now_date = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M:%S")
    # Process - STEP 1 - HARDWARE
    process_HARDWARE()
    # Process - STEP 2 - SOFTWARE
    process_SOFTWARE()
    # Process - STEP 3 - OTHERSOFTWARE
    process_OTHERSOFTWARE()
    # Return Name
    return str(org_id)+'--'+sys_hn+'--'


''' Tools
'''
def toolMkDir(name):
    # Creating Subdirectories
    try:
        if not os.path.exists(name):
            os.makedirs(name)
    except:
        print ("tsk_itop: Creating directory "+name+" failed")
        return -1
    # Done
    return 0

# Retrieves File List
def getFileList(path, ext):
    # Check incomming variable
    if path==None or ext==None:
        return []
    # Search directory
    dat=[]
    try:
        lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            nm=name.split('.')
            if not os.path.isdir(fn) and len(nm)>1 and nm[len(nm)-1].lower()==ext:
                dat.append(nm[0])
    # return list of files
    return dat



''' BootUp Preparations
'''
def bootup():
    # Creating Subdirectories
    err=toolMkDir(path_INBOX)
    if err != 0:
        return err
    err=toolMkDir(path_ARCHV)
    if err != 0:
        return err
    # Ready
    return 0

''' Process data file
'''
def toolProcess(name):
    # reading data file
    try:
        with open(os.path.join(path_INBOX, name+"."+ext_DAT), "rb") as f:
            data=f.read()
    except:
        print("tsk_itop: toolProcess access failed "+name)
        return -1
    # expanding data block
    try:
        zObj=zlib.decompressobj()
        zDat=zObj.decompress(data)
    except:
        print("tsk_itop: toolExpand decompress failed "+name)
        try:
            # atomic file rename for Linux not Windows OS
            os.rename(os.path.join(path_INBOX, name+"."+ext_DAT),
                      os.path.join(path_INBOX, name+"."+ext_ERR))
        except:
            print("tsk_itop: toolExpand rename DAT->ERR failed "+name)
            return -2
        # That's no compressed data file
        return -3
    # Renaming data file
    # Uncomment/Comment for Productive/Testing 
    try:
        # atomic file rename for Linux not Windows OS
        os.rename(os.path.join(path_INBOX, name+"."+ext_DAT),
                  os.path.join(path_INBOX, name+"."+ext_OCS))
    except:
        print("tsk_itop: toolExpand rename DAT->OCS failed "+name)
        return -4
    # Creating XML data file
    try:
        with open(os.path.join(path_ARCHV, name+"."+ext_XML), "wb") as f:
            f.write(zDat)
    except:
        print("tsk_itop: toolExpand creating XML file failed "+name)        
        return -5
    # everything ready
    return 0


''' Scan INBOX for new data files
'''
def toolScanInbox():
    # Get list of new data files
    lst=getFileList(path_INBOX, ext_DAT)
    # Sort file list
    lst.sort()
    # Process each entry
    for ety in lst:
        # Process
        print ("tsk_iTop: processing DAT file "+ety)
        if toolProcess(ety)<0:
            continue
        # Extract
        print("tsk_iTop: processing XML data")
        tags=toolExtract(os.path.join(path_ARCHV, ety+"."+ext_XML))
    #   print(tags)
        # Update
        print("tsk_iTop: Updating database")
        name=toolUpdate(tags)
        # Rename archive file
        if name==None:
            continue
        try:
            os.rename(os.path.join(path_ARCHV, ety+"."+ext_XML),
                      os.path.join(path_ARCHV, name+ety+"."+ext_XML))
        except:
            print("tsk_itop: rename failed for "+name)
    # Ready    
    return 0
 

''' Conversion Startup
'''
if __name__ == '__main__':
    # SHOW PATH
    print ('tsk_itop: Path - ',sys.argv[0])
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    print ("tsk_itop: running from - ", dirname)
    os.chdir(dirname)

    # SHOW USER ID
    print ('tsk_itop: Real UserID - %d' % os.getuid())
    print ('tsk_itop: Effective UserID - %d' % os.geteuid())

    # Processing config file
    if not readConfigFile():
        print ('tsk_itop: ERROR config file - ', cfg_file)
        exit (1)
    print('tsk_itop: CR iTop  - ', cfg_itop_cr )
    print('tsk_itop: CR mySQL - ', cfg_mysql_cr)

    # Bootup Preparations
    err=bootup()
    if err != 0:
        print ('tsk_itop: ERROR directory access - %d' % err)
        exit (err)

    # iTop Request IP ADDRESS
    if not iTopQuery_IpAddress():
        print ('tsk_itop: ERROR iTop request failed - IPv4Address')
        exit (3)
    # iTop Request IP RANGE
    if not iTopQuery_IpRange():
        print ('tsk_itop: ERROR iTop request failed - IPv4Range')
        exit (2)
    # iTop Request VirtualMachine
    if not iTopQuery_VirtualMachine():
        print ('tsk_itop: ERROR iTop request failed - VirtualMachine')
        exit(3)
    # iTop Request Software
    if not iTopQuery_Software():
        print ('tsk_itop: ERROR iTop request failed - Software')
        exit(4)
    # CleanUp Base Tables
    toolCleanUp()
    # Scanning Data Files
    err=toolScanInbox()

    # Running iTop Data Transfer
    if err==0:
        # Info
        print('tsk_itop: iTop Update', file=sys.stdout)
        # BUILD UPDATE COMMAND
        cmd=('cd itop;php exec.php')
        print ('tsk_itop: UPDATE CMD ',cmd)
        sys.stdout.flush()
        sys.stderr.flush()
        os.system(cmd)

    # Exit Code
    exit (err)
