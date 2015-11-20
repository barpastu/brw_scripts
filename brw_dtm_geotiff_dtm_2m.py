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


#year = "1993"
gsd = "2.00"
aufloesung="200_cm"
colorisation = "gray"
theme = "dtm"

##Settings for RestService
#proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
#auth = urllib2.HTTPBasicAuthHandler()
#opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
#urllib2.install_opener(opener)

#Logger for warnings and errors
logger_error = logging.getLogger('brw_error')
handler_error = logging.FileHandler('log_brw_error_dtm.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error) 
logger_error.setLevel(logging.WARNING)

#Logger for notices
logger_notice = logging.getLogger('brw')
handler_notice = logging.FileHandler('log_brw_dtm.log')
handler_notice.setFormatter(formatter)
logger_notice.addHandler(handler_notice) 
logger_notice.setLevel(logging.INFO)




#Start calculations
logger_notice.info("Start " + theme + " geotiff_dtm_2m bilinear")


#Settings for resampling-methode and vrt-path
method = 'bilinear'
path_old_location = "/home/barpastu/Geodaten/LV03/" + theme + "/geotiff_dtm_2m"
path_new_location="/home/barpastu/Geodaten/LV95/" + theme + "/geotiff_dtm_2m"
path_lv03 = path_old_location
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 
orthofilename = theme + "_geotiff_dtm_2m"
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
if not os.path.exists(path_lv03 + "/working/"):
    os.makedirs(path_lv03 + "/working/rename/")
    for i in os.listdir(path_old_location + "/"):
        if i.endswith(".tif"):
            cmd = "gdal_translate -of GTiff -co 'TILED=YES' -a_srs EPSG:21781  " +path_old_location + "/"
            cmd += i + " " + path_lv03 + "/working/rename/" + os.path.basename(i)
            os.system(cmd)



#Remove overviews
for i in os.listdir(path_lv03 + "/working/rename/"):
    cmd = "gdaladdo -clean " + path_lv03+ "/working/rename/" + os.path.basename(i)
    os.system(cmd)

#Minimize tiff-files
for infileNameFile_jpeg in os.listdir(os.path.join(path_lv03,"working","rename")) :
    #Splits up the tiff-file (to decrease the file size (without overviews))
    cmd = "tiffsplit " + os.path.join(path_lv03,"working/rename", infileNameFile_jpeg) + " tmp-"
    os.system(cmd)
    # Duplicate the geotransform and projection metadata from one raster dataset to another
    cmd = "python gdalcopyproj.py " + os.path.join(path_lv03,"working/rename", infileNameFile_jpeg) + " tmp-aaa.tif"
    os.system(cmd)
    cmd = "mv tmp-aaa.tif "+ os.path.join(path_lv03,"working/rename", infileNameFile_jpeg)
    os.system(cmd)


#Definition of spatial reference systems
S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

ogr.UseExceptions() 

#Create Tileindex
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + "old.shp " 
cmd += path_lv03 + "/working/rename/*.tif"
os.system(cmd)

#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + "old.shp")
layer = shp.GetLayer(0)

# Rename Files
for feature in layer:
    infileName = feature.GetField('location')
    #print infileName
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 + 2000000)
    minY = int(env[2] + 0.001 + 1000000)
    maxX = int(env[1] + 0.001 + 2000000)
    maxY = int(env[3] + 0.001 + 1000000)
    
    infileNameFile_jpeg = os.path.basename(infileName)  
    outfileName_jpeg = os.path.basename(infileName)
    
    #cmd = "mv " + infileName + " " + path_lv03 + "/working/"+infileNameFile_jpeg
    #os.system(cmd)

    #set color of nodata-values from black to white
    cmd ="gdalwarp -co TILED=YES -srcnodata -99999 "
    cmd += infileName + " " + path_lv03 + "/working/"+infileNameFile_jpeg
    os.system(cmd)
    


#Create Tileindex
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)


#Create vrt 
#add alphaband for extracting nodata-values
cmd = "gdalbuildvrt -srcnodata \"-99999\" -addalpha -vrtnodata None " + path_lv03 + "/" + orthofilename + "_alpha.vrt " + path_lv03 + "/working/*.tif"
os.system(cmd)

#set color of nodata-values from black to white
cmd ="gdalwarp -co ALPHA=YES "
cmd += "-wo NUM_THREADS=ALL_CPUS -co PHOTOMETRIC=MINISBLACK -co TILED=YES "
cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
cmd += "-co PREDICTOR=2" 
cmd += " -r " + method + " " + path_lv03 + "/" + orthofilename + "_alpha.vrt " + path_lv03 + "/" + orthofilename + "_white.tif"
os.system(cmd)


#extract grey-band
cmd ="gdal_translate -b 1 " + path_lv03 + "/" + orthofilename + "_white.tif " + path_lv03 + "/" + orthofilename + ".vrt "
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
    
    infileNameFile_jpeg = os.path.basename(infileName)  
    outfileName_jpeg = os.path.basename(infileName)



    # Transformieren 
    cmd = "gdalwarp -srcnodata \"-99999\"   -s_srs \"" + S_SRS + "\" -t_srs \"" + T_SRS + "\" -te "  + str(minX) + " "  
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
    #print("Files kopieren")
    #print(os.path.getsize(path_lv95 + "/ohne_overviews/" + outfileName_jpeg))





if vrt_exists is False:
    #print("vrt erstellen")
    #Create vrt
    cmd = "gdalbuildvrt " +vrt_95 + " " + path_lv95 + "/ohne_overviews/*.tif"
    os.system(cmd)
    #print ("vrt erstellt")


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    print ("***_***_*___*_" + infileName + "****_****_***")
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 )
    minY = int(env[2] + 0.001 )
    maxX = int(env[1] + 0.001 )
    maxY = int(env[3] + 0.001 )

    middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
    middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2
    
    infileNameFile_jpeg = os.path.basename(infileName)  
    outfileName_jpeg = os.path.basename(infileName)
    
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
    #print (cmd)

    #print (cmd + " erledigt") 
    #Ausschnitt generieren LV03
    cmd = " gdalwarp -co PHOTOMETRIC=MINISBLACK -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
    cmd += " -te " + str(minX) + " " + str(minY) + " " 
    cmd += str(maxX) + " " + str(maxY) + " "
    cmd +=os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
    cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)
    #print ("********"+cmd)
    #print("lv03")

 

    different_image_size = False
    

    cmd = "cp " + os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
    cmd += path_lv03 +"/"
    os.system(cmd)
    cmd = "cp " + os.path.join(path_lv03,"working", infileNameFile_jpeg) + " "
    cmd += path_lv03 + "/"
    os.system(cmd)
    cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
    cmd += path_lv95 + "/"
    os.system(cmd)
    cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) 
    cmd += " " + path_lv95 + "/"
    os.system(cmd)



    # generate Overviews 
    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE --config PHOTOMETRIC_OVERVIEW MINISBLACK --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv95 + "/" + outfileName_jpeg + " 2 4 8 16 32 64 128"
    os.system(cmd) 
    #print("overviews generieren")
    #print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))


    if different_image_size is False:

        #Calculate Difference
        cmd = "gdal_calc.py -A " 
        cmd += os.path.join(path_lv03,"working", "ausschnitt_"+infileNameFile_jpeg) + " -B " 
        cmd += os.path.join(path_lv95, "ohne_overviews","ausschnitt_"+outfileName_jpeg)+ " " 
        cmd += "--outfile=" +os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        cmd += " --calc=\"A-B\""
        os.system(cmd)
        
        #Differences<0.1 are right, else wrong/false
        cmd = "gdal_calc.py -A "+os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg) + " "
        cmd += "--outfile=" + os.path.join(path_lv95,"difference",outfileName_jpeg) + " "
        cmd += "--calc=\"(absolute(A)<=1)*0 + (absolute(A)>1)*1\" --NoDataValue=0"
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

    else :
        cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
        cmd += " " + os.path.join(path_lv95,"difference")
        os.system(cmd)
        logger_error.error(os.path.join(path_lv95,outfileName_jpeg)+" kann nicht verglichen werden, da unterschiedliche Bildgroessen")


cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
#os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
#os.system(cmd)
#cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
#os.system(cmd)

logger_notice.info("Ende")
