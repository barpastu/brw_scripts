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


year = "2014"
year_short = "14"
gsd = "0.125"
aufloesung="12_5cm"
colorisation = "rgb"


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
logger_notice.info("Start " + year)


##Settings 

#resampling-methode
method = 'lanczos'

#path to LV03-Data
path_old_location = "/home/barpastu/Geodaten/LV03/ortho" + year_short + "/" + aufloesung + "/" + colorisation

#path to LV95-Data (without colorisation and resolution)
path_new_location="/home/barpastu/Geodaten/LV95/orthofoto/" + year

#path to LV03-Data
path_lv03 = path_old_location 

#path to LV95-Data
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 

#Filename of vrt
orthofilename = "ortho"+year

#path to lv03-vrt
vrt = path_lv03 + "/" + orthofilename+".vrt"

#path to lv95-vrt
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"

#settings for check
height_extract = 500
vrt_exists = False





#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do a check for each tile
for feature in layer:
    infileName = feature.GetField('location')
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 + 2000000)
    minY = int(env[2] + 0.001 + 1000000)
    maxX = int(env[1] + 0.001 + 2000000)
    maxY = int(env[3] + 0.001 + 1000000)

    middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
    middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2
    
    infileNameFile_jpeg = str(minX)[1:4] + str(minY)[1:4] + "_"+aufloesung+".tif"   
    outfileName_jpeg = str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 
    
    #Create URL for RestService 
    #Lower left Corner (gets transformed coordinates from reframe)
    url_ll = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting="
    url_ll += str(middleX - height_extract) + "&northing=" + str(middleY - height_extract) 
    url_ll += "&format=json"
    response_ll = requests.get(url_ll)
    data_ll = response_ll.json()
    xmin_st = data_ll.values()[0]
    ymin_st = data_ll.values()[1]
    
    #Upper right Corner (gets transformed coordinates from reframe)
    url_ur = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting=" 
    url_ur += str(middleX + height_extract) + "&northing=" + str(middleY + height_extract)
    url_ur +="&format=json"
    response_ur = requests.get(url_ur)
    data_ur = response_ur.json()
    xmax_st = data_ur.values()[0]
    ymax_st = data_ur.values()[1]

    #Ausschnitt generieren LV95
    cmd = "gdalwarp -co PHOTOMETRIC=RGB -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd + " -te "
    cmd += str(round(float(xmin_st),2)) + " " + str(round(float(ymin_st),2)) + " " 
    cmd += str(round(float(xmax_st),2)) + " " + str(round(float(ymax_st),2)) 
    cmd += " -co TILED=YES -r " + method + " " 
    cmd += vrt_95 + " "     
    cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
    os.system(cmd)

    #Ausschnitt generieren LV03
    cmd = " gdalwarp -co PHOTOMETRIC=RGB -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
    cmd += " -te " + str(middleX-height_extract) + " " + str(middleY-height_extract) + " " 
    cmd += str(middleX+height_extract) + " " + str(middleY+height_extract) + " "
    cmd +=os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
    cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)


    #if ausschnitt differe in size
    cmd = "identify -format \"%[fx:w]\" "
    cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
    cmd = cmd.split(" ")
    width_lv95=subprocess.check_output(cmd)
    width_lv95=width_lv95.replace('\n','')
    width_lv95=width_lv95.replace('\"','')
    
    cmd = "identify -format \"%[fx:h]\" "
    cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
    cmd = cmd.split(" ")
    height_lv95=subprocess.check_output(cmd)
    height_lv95=height_lv95.replace('\n','')
    height_lv95=height_lv95.replace('\"','')
    
    cmd = "identify -format \"%[fx:w]\" "
    cmd += os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    cmd = cmd.split(" ")
    width_lv03=subprocess.check_output(cmd)
    width_lv03=width_lv03.replace('\n','')
    width_lv03=width_lv03.replace('\"','')
    
    cmd = "identify -format \"%[fx:h]\" "
    cmd += os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    cmd = cmd.split(" ")
    height_lv03=subprocess.check_output(cmd)
    height_lv03=height_lv03.replace('\n','')
    height_lv03=height_lv03.replace('\"','')
    
    if int(width_lv95)!=int(width_lv03) or int(height_lv95)!=int(height_lv03) :
		different_image_size = True
    else :
		different_image_size = False
    
    
    #Compress LV95-Tiles and LV03-Tiles to jpeg if older than 2012
    if int(year)<=2012 :

         cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES -co PHOTOMETRIC=YCBCR "
         cmd += os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
         cmd += os.path.join(path_lv03, infileNameFile_jpeg)
         os.system(cmd)

         cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES -co PHOTOMETRIC=YCBCR " 
         cmd += os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
         cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
         os.system(cmd)

         cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES -co PHOTOMETRIC=YCBCR "
         cmd += os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
         cmd += os.path.join(path_lv95, outfileName_jpeg)
         os.system(cmd)

         cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES -co PHOTOMETRIC=YCBCR "
         cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) + " "
         cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
         os.system(cmd)

    if int(year)>2012 :
         cmd = "mv " + os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
         cmd += path_lv03 +"/"
         os.system(cmd)
         cmd = "cp " + os.path.join(path_lv03,"working", infileNameFile_jpeg) + " "
         cmd += path_lv03 + "/"
         #os.system(cmd)
         cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
         cmd += path_lv95 + "/"
         os.system(cmd)
         cmd = "mv " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) 
         cmd += " " + path_lv95 + "/"
         os.system(cmd)


    # generate Overviews 
    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE "
    cmd += "--config PHOTOMETRIC_OVERVIEW YCBCR "
    cmd += "--config GDAL_TIFF_OVR_BLOCKSIZE 512 " 
    cmd += path_lv95 + "/" + outfileName_jpeg + " 2 4 8 16 32 64 128"
    os.system(cmd) 


    #generate Overviews for newly compressed lv03-Tiles 
    if int(year)<=2012:
        cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE " 
        cmd += "--config INTERLEAVE_OVERVIEW PIXEL "
        cmd += "--config GDAL_TIFF_OVR_BLOCKSIZE 512 " 
        cmd += path_lv03 + "/" + infileNameFile_jpeg + " 2 4 8 16 32 64 128"
        os.system(cmd)

    if different_image_size is False:
        #Compare without tolerance
        cmd = "compare " 
        cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
        cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
        cmd += "-compose src " +os.path.join(path_lv95,"difference",outfileName_jpeg)
        os.system(cmd)
        #print ("compare 1")


        #Compare with a tolerance of 10%
        cmd = "compare -fuzz 10% " 
        cmd +=os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
        cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
        cmd += "-compose src " +os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
        os.system(cmd)
        #print ("compare 2")

        #Calculate false pixels on base of the comparison without tolerance
        cmd = "convert "+os.path.join(path_lv95,"difference",outfileName_jpeg)
        cmd += " -fill black +opaque srgba(241,0,30,0.8) -fill white -opaque srgba(241,0,30,0.8)"
        cmd += " -format \"%[fx:mean*100]\" info:"
        cmd = cmd.split(" ")
        false_pixel_percent=subprocess.check_output(cmd)
        false_pixel_percent=false_pixel_percent.replace('\n','')
        false_pixel_percent_orig=false_pixel_percent.replace('\"','')
    
        #Error-Message if percentage of comparison without tolerance is 0%
        if float(false_pixel_percent_orig) == 0 :
            logger_error.error(os.path.join(path_lv95,"difference",outfileName_jpeg)+" weist einen Anteil von 0% falscher Pixelwerte im 0-Toleranz-Bild auf." )
            cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
            cmd += " " + os.path.join(path_lv95,"difference")
            os.system(cmd)
    

        #Calculate false pixels on base of the comparison with a tolerance of 10%
        cmd = "convert "+os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
        cmd += " -fill black +opaque srgba(241,0,30,0.8) -fill white -opaque srgba(241,0,30,0.8)"
        cmd += " -format \"%[fx:mean*100]\" info:"
        cmd = cmd.split(" ")
        false_pixel_percent=subprocess.check_output(cmd)
        false_pixel_percent=false_pixel_percent.replace('\n','')
        false_pixel_percent=false_pixel_percent.replace('\"','')
        logger_notice.info("Anteil falscher Pixelwerte: " +false_pixel_percent )

        #Error-Message if percentage of comparison with tolerance is higher than 1%
        if float(false_pixel_percent)>=1 :
            logger_error.error(os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)+" weist einen Anteil von mehr als 1% falscher Pixelwerte auf. Folgender Anteil: "+false_pixel_percent)
            cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
            cmd += " " + os.path.join(path_lv95,"difference")
            os.system(cmd)
    
        #remove comparison-images if percentage of comparison without tolerance is higher than 0 %
        # and percentage of comparison with tolerance is lower than 1%
        if float(false_pixel_percent_orig) > 0 and float(false_pixel_percent)<1 :
            cmd = "rm " + os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference",outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
            os.system(cmd)
    else :
        cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
        cmd += " " + os.path.join(path_lv95,"difference")
        os.system(cmd)
        logger_error.error(os.path.join(path_lv95,outfileName_jpeg)+" kann nicht verglichen werden, da unterschiedliche Bildgroessen")
        
        
cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
#os.system(cmd)
cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
os.system(cmd)

logger_notice.info("Ende")

