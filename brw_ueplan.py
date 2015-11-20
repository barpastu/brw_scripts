#!/usr/bin/python
# -*- coding: utf-8 -*-
#Check with lv03-Tile (test overlapping )

from osgeo import gdal
from osgeo import ogr, osr
import os
import requests
import json
import subprocess
import logging
#import urllib2


year ="2015"
gsd = "0.25"
aufloesung="25cm"
colorisation = "rgb"


##Settings for RestService
#proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
#auth = urllib2.HTTPBasicAuthHandler()
#opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
#urllib2.install_opener(opener)


#Logger for warnings and errors
logger_error = logging.getLogger('brw_error')
handler_error = logging.FileHandler('log_brw_error.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error) 
logger_error.setLevel(logging.WARNING)

#Logger for notices
logger_notice = logging.getLogger('brw')
handler_notice = logging.FileHandler('log_brw.log')
handler_notice.setFormatter(formatter)
logger_notice.addHandler(handler_notice) 
logger_notice.setLevel(logging.INFO)




#Start calculations
logger_notice.info("Start ueplan" )


##Settings 


#path to LV03-Data
path_old_location = "/home/barpastu/Geodaten/LV03/ueplan/up10h"

#path to LV95-Data (without colorisation and resolution)
path_new_location="/home/barpastu/Geodaten/LV95/ueplan"

#path to LV03-Data
path_lv03 = path_old_location 

#path to LV95-Data
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 






#Create Folders
if not os.path.exists(path_lv95):
    os.makedirs(path_lv95)



#Copy files to new folder (original-data)
for i in os.listdir(path_old_location + "/"):
    if i.endswith(".tfw"):
        cmd = "awk 'NR==5 {print \"             2\"$1};NR==6 {print \"             1\"$1};NR!=5&&NR!=6 {print}' "
        cmd += path_old_location + "/" + i + ">" + path_lv95 + "/" + i 
        os.system(cmd)
for i in os.listdir(path_old_location + "/"):
    if i.endswith(".tif"):
        cmd = "cp " + path_old_location + "/" + i + " " + path_lv95 + "/" + i
        os.system(cmd)




