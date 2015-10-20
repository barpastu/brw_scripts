#!/usr/bin/python
# -*- coding: utf-8 -*-
#Check with lv03-Tile (test overlapping )

from osgeo import gdal
from osgeo import ogr, osr
import os
import urllib2
import json
import subprocess
import logging


year = "2015"
month = "07"
gsd = "0.10"
aufloesung="10_cm"
colorisation = "rgb"

#Settings for RestService
proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
auth = urllib2.HTTPBasicAuthHandler()
opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
urllib2.install_opener(opener)

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


#Settings for resampling-methode and vrt-path
method = 'lanczos'
path_old_location = "lv03/drohnenbilder/" + year + "_" + month
path_new_location="lv95/drohnenbilder/" + year + "_" + month
path_lv03 = path_old_location
path_lv95 = path_new_location
orthofilename = "ortho_drohne_"+year + "_" +month
vrt = path_lv03 + "/" + orthofilename+".vrt"
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"
height_extract = 500
vrt_exists = False

#Definition of spatial reference systems
S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

ogr.UseExceptions() 

#Create Folders
if not os.path.exists(path_lv95):
    os.makedirs(path_lv95)
if not os.path.exists(path_lv95 + "/difference"):
    os.makedirs(path_lv95 + "/difference")
if not os.path.exists(path_lv95 + "/ohne_overviews"):
    os.makedirs(path_lv95 + "/ohne_overviews")


#Copy files to new folder (working-data)
if not os.path.exists(path_lv03 + "/working/"):
    os.makedirs(path_lv03 + "/working/")
    for i in os.listdir(path_old_location + "/"):
        if i.endswith(".tif"):
			#Stich together if geotiff is splitted up to tif and tfw
            if int(year)<2014 :
                cmd = "gdal_translate -of GTiff -co 'TILED=YES' -a_srs EPSG:21781 " +path_old_location + "/"
                cmd += i + " " + path_old_location  + "/working/" + os.path.basename(i)
            else :
                cmd = "cp " + path_old_location + "/" + i + " " + path_old_location + "/working/" + i
            print (cmd)
            os.system(cmd)
        #exit()




#Remove overviews in working-data
for i in os.listdir(path_lv03 + "/working/"):
    if i.endswith(".tif"):
        cmd = "gdaladdo -clean " + path_lv03 + "/working/" +i
        os.system(cmd)
        continue
    else:
        continue


#Minimize tiff-files
for infileNameFile_jpeg in os.listdir(os.path.join(path_lv03,"working")) :
    #Splits up the tiff-file (to decrease the file size (without overviews))
    cmd = "tiffsplit " + os.path.join(path_lv03,"working", infileNameFile_jpeg) + " tmp-"
    os.system(cmd)
    # Duplicate the geotransform and projection metadata from one raster dataset to another
    cmd = "python gdalcopyproj.py " + os.path.join(path_lv03,"working", infileNameFile_jpeg) 
    cmd += " tmp-aaa.tif"
    os.system(cmd)
    #Rename File
    cmd = "mv tmp-aaa.tif "+ os.path.join(path_lv03,"working", infileNameFile_jpeg)
    os.system(cmd)



#Create Tileindex for renaming files
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + "old.shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)

#Shape-File with tile division for renaming files
shp = ogr.Open(path_lv03 + "/" + orthofilename + "old.shp")
layer = shp.GetLayer(0)

# Do for each tile renaming files
for feature in layer:
    infileName = feature.GetField('location')
    print infileName
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


#Create Tileindex with renamed files
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)


#Create vrt with renamed files
cmd = "gdalbuildvrt " + path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/working/*.tif"
os.system(cmd)


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)



# Transformation for each tile
for feature in layer:
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

    minX_buffer = int(env[0] + 0.001-2)
    minY_buffer = int(env[2] + 0.001-2)
    maxX_buffer = int(env[1] + 0.001+2)
    maxY_buffer = int(env[3] + 0.001+2)
    
    infileNameFile_jpeg = str(minX)[1:4] + str(minY)[1:4] + "_"+aufloesung+".tif"   
    outfileName_jpeg = str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 




    # Transformation 
    cmd = "gdalwarp -s_srs \"" + S_SRS + "\" -t_srs \"" + T_SRS + "\" -te "  + str(minX) + " "  
    cmd += str(minY) + " " +  str(maxX) + " " +  str(maxY) + " -tr " + gsd + " " + gsd + " "
    cmd += "-wo NUM_THREADS=ALL_CPUS -co PHOTOMETRIC=RGB -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2" 
    cmd += " -r " + method + " " + vrt + " " + path_lv95 + "/" + outfileName_jpeg
    os.system(cmd)
    print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))

    #Set SRID
    cmd = "gdal_edit.py -a_srs EPSG:2056 " + path_lv95 + "/" +outfileName_jpeg
    os.system(cmd)
    print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))

    #log-Notice
    logger_notice.info(path_lv95 + "/" + outfileName_jpeg + " transformiert und zugeschnitten") 


    # Copy files to another folder for calculation
    cmd ="cp " + path_lv95 + "/" +outfileName_jpeg + " " + path_lv95 + "/ohne_overviews/"
    os.system(cmd)


#Create VRT of newly transformed data
if vrt_exists is False:
    #Create vrt
    cmd = "gdalbuildvrt " + path_lv95 + "/ohne_overviews/" + orthofilename + ".vrt " + path_lv95 
    cmd += "/ohne_overviews/*.tif"
    os.system(cmd)



#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Control
for feature in layer:
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
    outfileName_jpeg = str(minX)[0:4] + str(minY)[0:4] + "_"+aufloesung+".tif" 
    
    #Create URL for RestService 
    #Lower left Corner
    url_ll = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting="
    url_ll += str(middleX - height_extract) + "&northing=" + str(middleY - height_extract) 
    url_ll += "&format=json"
    response_ll = urllib2.urlopen(url_ll)
    data_ll = json.load(response_ll)
    xmin_st = data_ll.values()[0]
    ymin_st = data_ll.values()[1]
    
    #Upper right Corner
    url_ur = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?easting=" 
    url_ur += str(middleX + height_extract) + "&northing=" + str(middleY + height_extract)
    url_ur +="&format=json"
    response_ur = urllib2.urlopen(url_ur)
    data_ur = json.load(response_ur)
    xmax_st = data_ur.values()[0]
    ymax_st = data_ur.values()[1]

    #generate sample LV95
    cmd = "gdalwarp -co PHOTOMETRIC=RGB -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd + " -te "
    cmd += str(round(float(xmin_st),2)) + " " + str(round(float(ymin_st),2)) + " " 
    cmd += str(round(float(xmax_st),2)) + " " + str(round(float(ymax_st),2)) 
    cmd += " -co TILED=YES -r " + method + " " 
    #cmd += os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
    cmd += vrt_95 + " "     
    cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg)
    os.system(cmd)
 
    #generate sample LV03
    cmd = " gdalwarp -co PHOTOMETRIC=RGB -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
    cmd += " -te " + str(middleX-height_extract) + " " + str(middleY-height_extract) + " " 
    cmd += str(middleX+height_extract) + " " + str(middleY+height_extract) + " "
    cmd +=os.path.join(path_lv03,"working", infileNameFile_jpeg) + " " 
    cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)


    #Compress data
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

    

    # generate Overviews on lv95
    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE --config "
    cmd += "PHOTOMETRIC_OVERVIEW YCBCR --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv95 
    cmd += "/" + outfileName_jpeg + " 2 4 8 16 32 64 128"
    os.system(cmd) 


    #Compare
    cmd = "compare " 
    cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
    cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
    cmd += "-compose src " +os.path.join(path_lv95,"difference",outfileName_jpeg)
    os.system(cmd)


    #Compare with tolerances
    cmd = "compare -fuzz 10% " 
    cmd +=os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " " 
    cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
    cmd += "-compose src " +os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
    os.system(cmd)

    
    # Get percentage of false values
    cmd = "convert "+os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)
    cmd += " -fill black +opaque srgba(241,0,30,0.8) -fill white -opaque srgba(241,0,30,0.8)"
    cmd += " -format \"%[fx:mean*100]\" info:"
    cmd = cmd.split(" ")
    false_pixel_percent=subprocess.check_output(cmd)
    false_pixel_percent=false_pixel_percent.replace('\n','')
    false_pixel_percent=false_pixel_percent.replace('\"','')

    #Write logger notice
    logger_notice.info("Anteil falscher Pixelwerte: " +false_pixel_percent )
    
    #Write error message
    if float(false_pixel_percent)>=1:
      logger_error.error(os.path.join(path_lv95,"difference","fuzz_10_"+outfileName_jpeg)+" weist einen Anteil von mehr als 1% falscher Pixelwerte auf. Folgender Anteil: "+false_pixel_percent)
    
    #Remove sample-file
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

