from osgeo import gdal
from osgeo import ogr, osr
import os
#import urllib2
import json
import subprocess
import logging
import requests

year = "2014"
theme = "dom"
gsd = "0.50"
aufloesung="50cm"
colorisation = "gray"
tolerance="0.1"  #0.1m






##Settings


    
    
#path to the data on the old storage
path_new_location="/home/barpastu/Geodaten/LV95/lidar/"  + year + "/" + theme 

#path to the data on the new storage (LV95)
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 

#Filename of the vrt
orthofilename = theme+"_"+year



cmd = "gdaltindex -write_absolute_path " + path_lv95 + "/" + orthofilename + ".shp " 
cmd += path_lv95 + "/*.tif"
os.system(cmd)
print (cmd)

#Shape-File with tile division
shp = ogr.Open(path_lv95 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001)
    minY = int(env[2] + 0.001)
    maxX = int(env[1] + 0.001)
    maxY = int(env[3] + 0.001)
    
    middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
    middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2
        
    infileNameFile_jpeg = str(minX)[0:3] + str(minY)[0:3] + "_"+aufloesung+".tif"   
    outfileName_jpeg =  str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif"  

    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE --config PHOTOMETRIC_OVERVIEW MINISBLACK --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv95 + "/" + outfileName_jpeg + " 2 4 "
    os.system(cmd) 
