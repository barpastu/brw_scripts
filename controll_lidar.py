#!/usr/bin/python
# -*- coding: utf-8 -*-
#Check with lv03-Tile (test overlapping )

from osgeo import gdal
from osgeo import ogr, osr
import os
#import urllib2
import json
import subprocess
import logging
import requests

year = "2014"
theme = "hangneigung"
gsd = "0.50"
aufloesung="50cm"
colorisation = "gray"

##Settings for RestService
#proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
#auth = urllib2.HTTPBasicAuthHandler()
#opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
#urllib2.install_opener(opener)

#Logger for warnings and errors
logger_error = logging.getLogger('brw_error')
handler_error = logging.FileHandler('log_brw_error_lidar_'+theme+'.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error) 
logger_error.setLevel(logging.WARNING)

#Logger for notices
logger_notice = logging.getLogger('brw')
handler_notice = logging.FileHandler('log_brw_lidar_'+theme+'.log')
handler_notice.setFormatter(formatter)
logger_notice.addHandler(handler_notice) 
logger_notice.setLevel(logging.INFO)




#Start calculations
logger_notice.info("Start Lidar " + theme + " " + year)


##Settings

#resampling-method
if theme is "dtm" :
    #method = 'bilinear'
    method = 'lanczos'
if theme is "dom" :
    #method = 'near'
    method = 'lanczos'
if theme is "domdiff2001" :
    method = 'near'   #lanczos problematisch aufgrund abrupter Höhenänderungen z.B. Baum / kein Baum
if theme is "hangneigung" :
    method = 'lanczos'
if theme is "ndom" :
    method = 'lanczos'   #verschlirgt etwas
if theme is "dom_relief" :
    method = 'lanczos'
if theme is "dtm_relief" :
    method = 'lanczos'

#path_old_location = "lidar" + year + "/" + theme + "/" + aufloesung

#path to the data on the old storage
path_new_location="/home/barpastu/Geodaten/LV95/lidar/"  + year + "/" + theme 

#path to the data on the old storage
path_old_location="/home/barpastu/Geodaten/LV03/lidar"  + year + "/" + theme 


#path to the data on the new storage (LV03)
path_lv03 = path_old_location + "/" + aufloesung 

#path to the data on the new storage (LV95)
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 

#Filename of the vrt
orthofilename = theme+"_"+year

#path of the vrt
vrt = path_lv03 + "/" + orthofilename+".vrt"
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"
height_extract = 500
vrt_exists = False


#Create Tileindex
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)


#Create vrt 
cmd = "gdalbuildvrt " + path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/working/*.tif"
os.system(cmd)






if theme is not "dom":

    if vrt_exists is False:
        print("vrt erstellen")
        #Create vrt
        cmd = "gdalbuildvrt " + path_lv95 + "/ohne_overviews/" + orthofilename + ".vrt " + path_lv95 + "/ohne_overviews/*.tif"
        os.system(cmd)
        print ("vrt erstellt")


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    if theme is not "dom": 
        infileName = feature.GetField('location')
        print infileName
        geom = feature.GetGeometryRef()
        env = geom.GetEnvelope()

        minX = int(env[0] + 0.001 + 2000000)
        minY = int(env[2] + 0.001 + 1000000)
        maxX = int(env[1] + 0.001 + 2000000)
        maxY = int(env[3] + 0.001 + 1000000)
    
        middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
        middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2
    
        infileNameFile_jpeg = str(minX)[1:4] + str(minY)[1:4] + "_"+aufloesung+".tif"   
        outfileName_jpeg = theme +"_" +str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 
    
        #Create URL for RestService 
        #Lower left Corner (gets transformed coordinates from reframe)
        url_ll = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting="
        url_ll += str(minX) + "&northing=" + str(minY) 
        url_ll += "&format=json"
        response_ll = requests.get(url_ll)
        data_ll = response_ll.json()
        #response_ll = urllib2.urlopen(url_ll)
        #data_ll = json.load(response_ll)
        xmin_st = data_ll.values()[0]
        ymin_st = data_ll.values()[1]
    
        #Upper right Corner (gets transformed coordinates from reframe)
        url_ur = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting=" 
        url_ur += str(maxX) + "&northing=" + str(maxY)
        url_ur +="&format=json"
        response_ur = requests.get(url_ur)
        data_ur = response_ur.json()
        #response_ur = urllib2.urlopen(url_ur)
        #data_ur = json.load(response_ur)
        xmax_st = data_ur.values()[0]
        ymax_st = data_ur.values()[1]

        #Ausschnitt generieren LV95
        cmd = "gdalwarp -co PHOTOMETRIC=MINISBLACK -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd + " -te "
        cmd += str(round(float(xmin_st),2)) + " " + str(round(float(ymin_st),2)) + " " 
        cmd += str(round(float(xmax_st),2)) + " " + str(round(float(ymax_st),2)) 
        cmd += " -co TILED=YES -r " + method + " " 
        #cmd += os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
        cmd += vrt_95 + " "     
        cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
        os.system(cmd)

        print (cmd + " erledigt") 
        #Ausschnitt generieren LV03
        cmd = " gdalwarp -co PHOTOMETRIC=MINISBLACK -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
        cmd += " -te " + str(minX) + " " + str(minY) + " " 
        cmd += str(maxX) + " " + str(maxY) + " "
        cmd +=os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
        cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
        os.system(cmd)
        print ("********"+cmd)
        print("lv03")


        if int(year)>2012 :
             cmd = "cp " + os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
             cmd += path_lv03 +"/"
             #os.system(cmd)
             cmd = "cp " + os.path.join(path_lv03,"working", infileNameFile_jpeg) + " "
             cmd += path_lv03 + "/"
             #os.system(cmd)
             cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", theme + "_"+outfileName_jpeg) + " "
             cmd += path_lv95 + "/"
             os.system(cmd)
             cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) 
             cmd += " " + path_lv95 + "/"
             #os.system(cmd)


    #if int(year)<=2012 :
    #     infileNameFile=infileNameFile_jpeg
    #     outfileName =outfileName_jpeg
    #     outfileNamePath = outfileNamePath_jpeg


    # generate Overviews 
    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE --config PHOTOMETRIC_OVERVIEW MINISBLACK --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv95 + "/" + outfileName_jpeg + " 2 4 "
    os.system(cmd) 
    print("overviews generieren")
    
    if theme is not "dom":
        #Calculate Difference
        cmd = "gdal_calc.py -A " 
        cmd += os.path.join(path_lv03,"working", "ausschnitt_"+infileNameFile_jpeg) + " -B " 
        cmd += os.path.join(path_lv95, "ohne_overviews","ausschnitt_"+outfileName_jpeg)+ " " 
        cmd += "--outfile=" +os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        cmd += " --calc=\"A-B\""
        os.system(cmd)
        
        cmd = "gdalinfo -mm  " + os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        cmd += " | sed -ne 's/.*Computed Min\/Max=//p'| tr -d ' ' | cut -d ',' -f 1 | cut -d . -f 1"
        min_value=subprocess.check_output(cmd)
        
        cmd = "gdalinfo -mm  " + os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        cmd += " | sed -ne 's/.*Computed Min\/Max=//p'| tr -d ' ' | cut -d ',' -f 2 | cut -d . -f 1"
        max_value=subprocess.check_output(cmd)
        
        
        #Differences<0.1 are right, else wrong/false
        cmd = "gdal_calc.py -A "+os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg) + " "
        cmd += "--outfile=" + os.path.join(path_lv95,"difference",outfileName_jpeg) + " "
        cmd += "--calc=\"(absolute(A)<=0.1)*0 + (absolute(A)>0.1)*1\" --NoDataValue=10"
        os.system(cmd)

        cmd = "convert "+os.path.join(path_lv95,"difference",outfileName_jpeg)
        cmd += " -format \"%[fx:mean*100]\" info:"
        cmd = cmd.split(" ")
        false_pixel_percent=subprocess.check_output(cmd)
        false_pixel_percent=false_pixel_percent.replace('\n','')
        false_pixel_percent=false_pixel_percent.replace('\"','')
        #print repr(false_pixel_percent)
        logger_notice.info("Anteil falscher Pixelwerte: " +false_pixel_percent )


        if float(false_pixel_percent)>=1:
            logger_error.error(os.path.join(path_lv95,"difference",outfileName_jpeg)+" weist einen Anteil von mehr als 1% falscher Pixelwerte auf. Folgender Anteil: "+false_pixel_percent)
            logger_error.error(os.path.join(path_lv95,"difference",outfileName_jpeg)+" höchster Wert: "+str(max_value)+" ; niedrigster Wert: " + str(min_value))
            cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
            cmd += " " + os.path.join(path_lv95,"difference")
            os.system(cmd)
        else :
            cmd = "rm " + os.path.join(path_lv03, "working","ausschnitt_"+infileNameFile_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg)
            #os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference",outfileName_jpeg)
            os.system(cmd)



cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
#os.system(cmd)
cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
os.system(cmd)

logger_notice.info("Ende")

