import os
import cv2
import utilities as util
import geometry as gm
from pyproj import Proj
import subprocess
try:
    from osgeo import gdal
except ImportError:
    import gdal
import utm


class Combiner:
    def __init__(self,fileDIRMatrix_,dataMatrix_,CRS_):
        '''
        :param imageList_: List of all images DIR in dataset.
        :param dataMatrix_: Matrix with all pose data in dataset.
        :return:
        '''
        self.imageList = []
        self.tiffList=[]
        self.dataMatrix = dataMatrix_
        self.fileDIRMatrix=fileDIRMatrix_
        self.CRS=CRS_
        for i in range(0,len(self.fileDIRMatrix)):
            newImageName=self.fileDIRMatrix[i].replace('.JPG','.tif').replace("images","outputs")
            self.tiffList.append(newImageName)
            newtfwName=self.fileDIRMatrix[i].replace('.JPG','.tfw').replace("images","outputs")
            if os.path.exists(newImageName) and os.path.exists(newtfwName):
                    print("tiff generated from {} exists, skip georeferencing and creating twf file".format(self.dataMatrix[i][0]))
            else:
                image = (cv2.imread(self.fileDIRMatrix[i]))  #no downsample
                #image = imageList_[i][::2,::2,:] #downsample the image to speed things up. 4000x3000 is huge!
                M = gm.computeUnRotMatrix(self.dataMatrix[i,:])
                #Perform a perspective transformation based on pose information.
                #Ideally, this will mnake each image look as if it's viewed from the top.
                #We assume the ground plane is perfectly flat.
                correctedImage = gm.warpPerspectiveWithPadding(image,M)
                #save corrected image as tiff
                cv2.imwrite(newImageName,correctedImage)
                #tifffile.imsave(newImageName, correctedImage)
                #use gdal nearblack to remove black pixels
                gdal.Nearblack(newImageName, newImageName, format="GTiff", creationOptions= ["compress=jpeg"], setAlpha=True)
                #add projection spec to tiff, cmd: 
                add_prj_spec=["gdal_edit.py -a_srs {} {}".format(self.CRS,newImageName)]
                process = subprocess.Popen(add_prj_spec, stdout=subprocess.PIPE,shell=True)
                output, error = process.communicate()
                output=output.decode(encoding='UTF-8')
                if output=='':
                    print("successfully add projection CRS: {} to {}".format(self.CRS,self.dataMatrix[i][0]))
                else:
                    print("Oops, there's something wrong with add projection to tiff")
                #georeference tiff by creating .twf
                lat_dms=self.dataMatrix[i][1]
                lat_dms = lat_dms.replace("'",'').replace('"','').split(' ')
                if lat_dms[4]=="N":
                    lat_dd = util.dms_to_dd(lat_dms)
                else:
                    lat_dd = -util.dms_to_dd(lat_dms)
                lon_dms=self.dataMatrix[i][2]
                lon_dms = lon_dms.replace("'",'').replace('"','').split(' ')
                if lon_dms[4]=="E":
                    lon_dd = util.dms_to_dd(lon_dms)
                else:
                    lon_dd = -util.dms_to_dd(lon_dms)
                #print(lat_dd,lon_dd)
                #myProj = Proj("+proj=utm +zone=55 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
                UTMx, UTMy, zone,letter=utm.from_latlon(lat_dd,lon_dd)
                #myProj = Proj("+proj=utm +zone={} +zone_letter={} +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs".format(zone,letter))
                #UTMx, UTMy = myProj(lon_dd, lat_dd)
                fov_dd = float(self.dataMatrix[i][-1].split(" ")[0])
                relativeAltitude= float(self.dataMatrix[i][-2])
                img_width = image.shape[1]
                gsd = gm.get_gsd(fov_dd, relativeAltitude, img_width)
                refractive_index=1
                tfw=(str(gsd*refractive_index)+'\n0.0000000000\n0.0000000000\n-'+str(gsd*refractive_index)+'\n'+str(UTMx)+'\n'+str(UTMy))
                file=open(newtfwName,'w')
                file.write(str(tfw)) 
                file.close()  
                print('TFW file created for {}'.format(self.dataMatrix[i][0]))


    def createMosaic(self,dataDIR):
        # merge all raster tiffs into one with different compression settings. 
        # Check: https://gis.stackexchange.com/questions/1104/should-gdal-be-set-to-produce-geotiff-files-with-compression-which-algorithm-sh 
        # Check: https://gdal.org/drivers/raster/gtiff.html#creation-options
        input_jpgs=" ".join(self.fileDIRMatrix)
        input_tiffs=input_jpgs.replace('.JPG','.tif').replace("images","outputs")
        merge_tiff_dir=dataDIR/"merged.tif"
        gdal_merge=["gdal_merge.py -of GTiff -co BIGTIFF=IF_NEEDED -co COMPRESS=JPEG -co TILED=YES -co BLOCKXSIZE=256 -co BLOCKYSIZE=256 -o {} {}".format(merge_tiff_dir,input_tiffs)]
        process=subprocess.Popen(gdal_merge, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        output=output.decode(encoding='UTF-8')
        if 'done' in output:
            print("Successfully merged all tiffs")
        else:
            print("Merge failed, try again")
        create_overview=["gdaladdo -r nearest {}".format(merge_tiff_dir)]
        process=subprocess.Popen(create_overview, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        output=output.decode(encoding='UTF-8')
        if 'done' in output:
            print("Successfully created overviews")
        else:
            print("Create overview failed, try again")
        
        
    

