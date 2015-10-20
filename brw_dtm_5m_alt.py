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


year = "2014"
year_short = "14"
theme = "dtm_relief"
gsd = "5.00"
aufloesung="500_cm"
colorisation = "gray"

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
logger_notice.info("Start Lidar " + theme + " " + year + " " + gsd)


##Settings 

#resampling-method
method = 'lanczos'

#path to the data on the old storage
path_new_location="lidar/"  + year + "/" + theme 

#path to the data of gsd 50 cm on the new storage
path_lv03_50 = path_new_location + "/lv03/" + colorisation + "/50_cm"

#path to the data on the new storage (LV03)
path_lv03 =  path_new_location + "/lv03/"+ colorisation + "/" + aufloesung 

#path to the data on the new storage (LV95)
path_lv95 = path_new_location + "/lv95/"+ colorisation + "/" + aufloesung 

#Filename of the vrt
orthofilename = theme + "_5m_"+year

#path of the vrt
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
if not os.path.exists(path_lv03 + "/working/"):
    os.makedirs(path_lv03 + "/working/")



#Definition of spatial reference systems
S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

ogr.UseExceptions() 

#Create vrt LV95 (50_cm)
cmd = "gdalbuildvrt " + path_lv03 + "/" + orthofilename + "_50.vrt " + path_lv03_50 + "/*.tif"
os.system(cmd)


#Create Tileindex based on vrt LV95 (50_cm) --> only one tile
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/"  + orthofilename+"_50.vrt"
os.system(cmd)
print(cmd)


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
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

    
    outfileName_jpeg = orthofilename + "_5m.tif" 
    infileNameFile_jpeg = outfileName_jpeg

    # transformation to gsd = 5 m
    cmd = "gdalwarp -tr " + gsd + " " + gsd + " "
    cmd += "-wo NUM_THREADS=ALL_CPUS -co PHOTOMETRIC=MINISBLACK -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2" 
    cmd += " -r " + method + " " + path_lv03 + "/"  + orthofilename+"_50.vrt" + " "
    cmd += path_lv03 + "/" + infileNameFile_jpeg
    os.system(cmd)



    # transformieren from LV03 to LV95
    cmd = "gdalwarp -s_srs \"" + S_SRS + "\" -t_srs \"" + T_SRS + "\" -te "  + str(minX) + " "  
    cmd += str(minY) + " " +  str(maxX) + " " +  str(maxY) + " -tr " + gsd + " " + gsd + " "
    cmd += "-wo NUM_THREADS=ALL_CPUS -co PHOTOMETRIC=MINISBLACK -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2" 
    cmd += " -r " + method + " " + path_lv03 +"/" + infileNameFile_jpeg + " " + path_lv95 + "/" + outfileName_jpeg
    os.system(cmd)



    cmd = "gdal_edit.py -a_srs EPSG:2056 " + path_lv95 + "/" +outfileName_jpeg
    os.system(cmd)
    print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))


    logger_notice.info(path_lv95 + "/" + outfileName_jpeg + " transformiert und zugeschnitten") 


    cmd = "gdal_translate -co TILED=YES "
    cmd += "-co PROFILE=GeoTIFF -co INTERLEAVE=PIXEL -co COMPRESS=DEFLATE "  
    cmd += "-co PREDICTOR=2"
    #os.system(cmd)

    # Files in anderen Ordner kopieren
    cmd ="cp " + path_lv95 + "/" +outfileName_jpeg + " " + path_lv95 + "/ohne_overviews/"
    os.system(cmd)
    #print("Files kopierien")
    print(os.path.getsize(path_lv95 + "/ohne_overviews/" + outfileName_jpeg))

    if theme is not "dom":

        if vrt_exists is False:
            print("vrt erstellen")
            #Create vrt
            cmd = "gdalbuildvrt " + path_lv95 + "/ohne_overviews/" + orthofilename + ".vrt " + path_lv95 + "/ohne_overviews/*.tif"
            os.system(cmd)
            print ("vrt erstellt")


    
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
        cmd += " -te " + str(middleX-height_extract) + " " + str(middleY-height_extract) + " " 
        cmd += str(middleX+height_extract) + " " + str(middleY+height_extract) + " "
        cmd +=os.path.join(path_lv03, infileNameFile_jpeg) + " " 
        cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
        os.system(cmd)
        print ("********"+cmd)
        print("lv03")

        if int(year)<=2012 :

             cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES "
             cmd += os.path.join(path_lv03, infileNameFile_jpeg) + " " 
             cmd += os.path.join(path_lv03, infileNameFile_jpeg)
             os.system(cmd)

             cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES " 
             cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " "
             cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
             os.system(cmd)

             cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES "
             cmd += os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
             cmd += os.path.join(path_lv95, outfileName_jpeg)
             os.system(cmd)

             cmd = "gdal_translate -co COMPRESS=JPEG -co TILED=YES "
             cmd += os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) + " "
             cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
             os.system(cmd)

        if int(year)>2012 :
             cmd = "cp " + os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg) + " "
             cmd += path_lv03 +"/"
             os.system(cmd)
             cmd = "cp " + os.path.join(path_lv03, infileNameFile_jpeg) + " "
             cmd += path_lv03 + "/"
             os.system(cmd)
             cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", outfileName_jpeg) + " "
             cmd += path_lv95 + "/"
             os.system(cmd)
             cmd = "cp " + os.path.join(path_lv95, "ohne_overviews", "ausschnitt_"+outfileName_jpeg) 
             cmd += " " + path_lv95 + "/"
             os.system(cmd)


    #if int(year)<=2012 :
    #     infileNameFile=infileNameFile_jpeg
    #     outfileName =outfileName_jpeg
    #     outfileNamePath = outfileNamePath_jpeg


    # generate Overviews 
    #cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE --config PHOTOMETRIC_OVERVIEW MINISBLACK --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv95 + "/" + outfileName_jpeg + " 2 4 "
    #os.system(cmd) 
    #print("overviews generieren")
    #print(os.path.getsize(path_lv95 + "/" + outfileName_jpeg))


    #generate Overviews for newly compressed lv03-Tiles 
    #if int(year)<=2012:
        #cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE  --config INTERLEAVE_OVERVIEW PIXEL --config GDAL_TIFF_OVR_BLOCKSIZE 512 " + path_lv03 + "/" + infileNameFile_jpeg + " 2 4"
        #os.system(cmd)
        #print("overviews generieren lv03") 


        #Calculate Difference
        cmd = "gdal_calc.py -A " 
        cmd += os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg) + " -B " 
        cmd += os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)+ " " 
        cmd += "--outfile=" +os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        cmd += " --calc=\"A-B\""
        os.system(cmd)

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
        else :
            cmd = "rm " + os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
            os.system(cmd)
            cmd = "rm " + os.path.join(path_lv95,"difference",outfileName_jpeg)
            os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
os.system(cmd)
#cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
#os.system(cmd)

logger_notice.info("Ende")

