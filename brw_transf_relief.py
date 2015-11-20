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



gsd = "30"
aufloesung="30_m"
colorisation = "gray"

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
logger_notice.info("Start relief")


#Settings for resampling-methode and vrt-path
method = 'bilinear'  #near
path_old_location = "/home/barpastu/Geodaten/LV03/images/"
path_new_location="/home/barpastu/Geodaten/LV95/images/relief"
path_lv03 = path_old_location 
path_lv95 = path_new_location + "/" + aufloesung 
orthofilename = "relief"
vrt = path_lv03 + "/" + orthofilename+".vrt"
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"
height_extract = 500
vrt_exists = False


#Create Folders
if not os.path.exists(path_lv95):
    os.makedirs(path_lv95)
if not os.path.exists(path_lv95 + "/difference"):
    os.makedirs(path_lv95 + "/difference")
if not os.path.exists(path_lv95 + "/ohne_overviews"):
    os.makedirs(path_lv95 + "/ohne_overviews")





#Copy files to new folder (original-data)
if not os.path.exists(path_lv03 + "/original/"):
    os.makedirs(path_lv03 + "/original/")
    for i in os.listdir(path_old_location + "/"):
        if i.endswith("orig.tif"):
            cmd = "gdal_translate -of GTiff -co 'TILED=YES' -a_srs EPSG:21781 " +path_old_location + "/"
            cmd += i + " " + path_lv03 + "/original/" + os.path.basename(i)
            os.system(cmd)
        #exit()

if not os.path.exists(path_lv03 + "/working/"):
    os.makedirs(path_lv03 + "/working/")
    cmd = "cp " + path_lv03 + "/original/*.tif " + path_lv03 + "/working/"
    os.system(cmd) 

#Remove overviews
for i in os.listdir(path_lv03 + "/original/"):
    cmd = "gdal_translate -of GTiff -co 'TILED=YES' -expand gray " + path_lv03+ "/original/" + os.path.basename(i) + " " + path_lv03 + "/working/" + i 
    os.system(cmd)



#Definition of spatial reference systems
S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

ogr.UseExceptions() 

#Create Tileindex
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + "old.shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)

#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + "old.shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    #print infileName
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 + 2000000)
    minY = int(env[2] + 0.001 + 1000000)
    maxX = int(env[1] + 0.001 + 2000000)
    maxY = int(env[3] + 0.001 + 1000000)
    
    infileNameFile_jpeg = str(minX)[1:4] + str(minY)[1:4] + "_"+aufloesung+".tif"   
    outfileName_jpeg = str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 


    cmd = "mv " + infileName + " " + path_lv03 + "/working/"+infileNameFile_jpeg
    os.system(cmd)


#Create Tileindex
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)


#Create vrt 
cmd = "gdalbuildvrt  " + path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/working/*.tif"
os.system(cmd)



#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)



# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    #print infileName
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 + 2000000)
    minY = int(env[2] + 0.001 + 1000000)
    maxX = int(env[1] + 0.001 + 2000000)
    maxY = int(env[3] + 0.001 + 1000000)

    middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
    middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2

    minX_buffer = int(env[0] + 0.001-2)
    minY_buffer = int(env[2] + 0.001-2)
    maxX_buffer = int(env[1] + 0.001+2)
    maxY_buffer = int(env[3] + 0.001+2)
    
    infileNameFile_jpeg = str(minX)[1:4] + str(minY)[1:4] + "_"+aufloesung+".tif"   
    outfileName_jpeg = str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 



    # Transformieren 
    cmd = "gdalwarp -dstnodata \"255,255,255\" -s_srs \"" + S_SRS + "\" -t_srs \"" + T_SRS + "\" -te "  + str(minX) + " "  
    cmd += str(minY) + " " +  str(maxX) + " " +  str(maxY) + " -tr " + gsd + " " + gsd + " "
    cmd += "-wo NUM_THREADS=ALL_CPUS -co PHOTOMETRIC=MINISBLACK -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2" 
    cmd += " -r " + method + " " + vrt + " " + path_lv95 + "/" + outfileName_jpeg
    os.system(cmd)
    #print(cmd)
    #print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))



    cmd = "gdal_edit.py -a_srs EPSG:2056 " + path_lv95 + "/" +outfileName_jpeg
    os.system(cmd)
    #print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))


    logger_notice.info(path_lv95 + "/" + outfileName_jpeg + " transformiert und zugeschnitten") 


    cmd = "gdal_translate -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2"
    #os.system(cmd)

    # Files in anderen Ordner kopieren
    cmd ="cp " + path_lv95 + "/" +outfileName_jpeg + " " + path_lv95 + "/ohne_overviews/"
    os.system(cmd)
    #print("Files kopierien")
    #print(os.path.getsize(path_lv95 + "/ohne_overviews/" + outfileName_jpeg))




if vrt_exists is False:
    #print("vrt erstellen")
    #Create vrt
    cmd = "gdalbuildvrt " + path_lv95 + "/ohne_overviews/" + orthofilename + ".vrt " + path_lv95 + "/ohne_overviews/*.tif"
    os.system(cmd)
    #print ("vrt erstellt")


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    #print infileName
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 )
    minY = int(env[2] + 0.001 )
    maxX = int(env[1] + 0.001 )
    maxY = int(env[3] + 0.001 )

    middleX = (int(minX + 0.001)+int(maxX + 0.001 ))/2
    middleY = (int(minY + 0.001)+int(maxY + 0.001 ))/2
    
    infileNameFile_jpeg = str(minX)[0:3] + str(minY)[0:3] + "_"+aufloesung+".tif"   
    outfileName_jpeg = "2" + str(minX)[0:3] + "1" + str(minY)[0:3] + "_"+aufloesung+".tif" 
    
    #Create URL for RestService 
    #Lower left Corner
    url_ll = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting="
    url_ll += str(minX) + "&northing=" + str(minY) 
    url_ll += "&format=json"
    response_ll = requests.get(url_ll)
    data_ll = response_ll.json()
    #response_ll = urllib2.urlopen(url_ll)
    #data_ll = json.load(response_ll)
    xmin_st = data_ll.values()[0]
    ymin_st = data_ll.values()[1]

    #Upper right Corner
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

    #print (cmd + " erledigt") 
    #Ausschnitt generieren LV03
    cmd = " gdalwarp -co PHOTOMETRIC=MINISBLACK -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
    cmd += " -te " + str(minX) + " " + str(minY) + " " 
    cmd += str(maxX) + " " + str(maxY) + " "
    cmd +=os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
    cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)


#    cmd = "cp " + os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
#    cmd += path_lv03 +"/"
#    os.system(cmd)
#    cmd = "cp " + os.path.join(path_lv03,"working", infileNameFile_jpeg) + " "
#    cmd += path_lv03 + "/"
#    os.system(cmd)
#    cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
#    cmd += path_lv95 + "/"
#    os.system(cmd)
#    cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) 
#    cmd += " " + path_lv95 + "/"
#    os.system(cmd)

    cmd = "gdal_translate -co COMPRESS=PACKBITS -co TILED=YES -co PHOTOMETRIC=MINISBLACK "
    cmd += os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
    cmd += os.path.join(path_lv03, infileNameFile_jpeg)
    os.system(cmd)

    cmd = "gdal_translate -co COMPRESS=PACKBITS -co TILED=YES -co PHOTOMETRIC=MINISBLACK " 
    cmd += os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
    cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)

    cmd = "gdal_translate -co COMPRESS=PACKBITS -co TILED=YES -co PHOTOMETRIC=MINISBLACK "
    cmd += os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
    cmd += os.path.join(path_lv95, outfileName_jpeg)
    os.system(cmd)

    cmd = "gdal_translate -co COMPRESS=PACKBITS -co TILED=YES -co PHOTOMETRIC=MINISBLACK "
    cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) + " "
    cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
    os.system(cmd)


    #Compare
    cmd = "compare " 
    cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
    cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
    cmd += "-compose src " +os.path.join(path_lv95,"difference",outfileName_jpeg)
    os.system(cmd)
    print ("compare 1")


    #Compare
    cmd = "compare -fuzz 10% " 
    cmd +=os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
    cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
    cmd += "-compose src " +os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
    #print ("*****"+cmd)
    os.system(cmd)
    #print ("compare 2")

    
    # Get percentage of false values
    cmd = "convert "+os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
    cmd += " -fill black +opaque  \"srgba(241,0,30,0.8)\" -fill white -opaque "
    cmd += "\"srgba(241,0,30,0.8)\""
    cmd += " -format \"false pixel values = %[fx:mean*100] %\"  info:"
    #os.system(cmd)

    cmd = "convert "+os.path.join(path_lv95,"difference",outfileName_jpeg)
    cmd += " -fill black +opaque srgba(241,0,30,0.8) -fill white -opaque srgba(241,0,30,0.8)"
    cmd += " -format \"%[fx:mean*100]\" info:"
    cmd = cmd.split(" ")
    false_pixel_percent=subprocess.check_output(cmd)
    false_pixel_percent=false_pixel_percent.replace('\n','')
    false_pixel_percent_orig=false_pixel_percent.replace('\"','')
    if float(false_pixel_percent_orig) == 0 :
        logger_error.error(os.path.join(path_lv95,"difference",outfileName_jpeg)+" weist einen Anteil von 0% falscher Pixelwerte im 0-Toleranz-Bild auf." )

    cmd = "convert "+os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
    cmd += " -fill black +opaque srgba(241,0,30,0.8) -fill white -opaque srgba(241,0,30,0.8)"
    cmd += " -format \"%[fx:mean*100]\" info:"
    cmd = cmd.split(" ")
    false_pixel_percent=subprocess.check_output(cmd)
    false_pixel_percent=false_pixel_percent.replace('\n','')
    false_pixel_percent=false_pixel_percent.replace('\"','')
    #print repr(false_pixel_percent)
    logger_notice.info("Anteil falscher Pixelwerte: " +false_pixel_percent )

    if float(false_pixel_percent)>=1:
      logger_error.error(os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)+" weist einen Anteil von mehr als 1% falscher Pixelwerte auf. Folgender Anteil: "+false_pixel_percent)

    cmd = "rm " + os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)
    cmd = "rm " + os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
    os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
#os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
#os.system(cmd)
#cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
#os.system(cmd)

logger_notice.info("Ende")

