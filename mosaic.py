import os
import cv2
import utilities as util
import geometry as gm
from pyproj import Proj
from pathlib import Path
import subprocess
try:
    from osgeo import gdal
except ImportError:
    import gdal
import utm
import threading

class georeferenceImageThread (threading.Thread):
    def __init__(self, threadID, name, i, dataMatrix, CRS, refractiveIndex):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.i = i
        self.dataMatrix = dataMatrix
        self.CRS = CRS
        self.refractiveIndex = refractiveIndex

    def georeferenceImage(self):
        newImageName=self.dataMatrix[0].replace('.JPG','.tif').replace("images","outputs")
        newtfwName=self.dataMatrix[0].replace('.JPG','.tfw').replace("images","outputs")
        if os.path.exists(newImageName) and os.path.exists(newtfwName):
                print("tiff generated from {} exists, skip georeferencing and creating twf file".format(self.dataMatrix[0]))
        else:
            image = (cv2.imread(self.dataMatrix[0]))  #no downsample
            #image = imageList_[i][::2,::2,:] #downsample the image to speed things up. 4000x3000 is huge!
            # get pose from yaw pitch roll
            poses=[float(pose) for pose in self.dataMatrix[4:7]]
            M = gm.computeUnRotMatrix(poses)
            #Perform a perspective transformation based on pose information.
            #Ideally, this will mnake each image look as if it's viewed from the top.
            #We assume the ground plane is perfectly flat.
            correctedImage = gm.warpPerspectiveWithPadding(image,M)
            #save corrected image as tiff
            cv2.imwrite(newImageName,correctedImage)
            #tifffile.imsave(newImageName, correctedImage)
            #use gdal nearblack to remove black pixels
            gdal.Nearblack(newImageName, newImageName, format="GTiff", creationOptions= ["compress=lzw"], setAlpha=True)
            #add projection spec to tiff, cmd: 
            add_prj_spec=["gdal_edit.py -a_srs {} {}".format(self.CRS,newImageName)]
            process = subprocess.Popen(add_prj_spec, stdout=subprocess.PIPE,shell=True)
            output, error = process.communicate()
            output=output.decode(encoding='UTF-8')
            if output=='':
                print("successfully add projection CRS: {} to {}".format(self.CRS,self.dataMatrix[0]))
            else:
                print("Oops, there's something wrong with add projection to tiff")
            #georeference tiff by creating .twf
            lat_dd=float(self.dataMatrix[2])
            lon_dd=float(self.dataMatrix[3])
            UTMx, UTMy, zone,letter=utm.from_latlon(lat_dd,lon_dd)
            #myProj = Proj("+proj=utm +zone={} +zone_letter={} +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs".format(zone,letter))
            #UTMx, UTMy = myProj(lon_dd, lat_dd)
            fov_dd = float(self.dataMatrix[-1].split(" ")[0])
            relativeAltitude= float(self.dataMatrix[-2])
            img_width = image.shape[1]
            gsd = gm.get_gsd(fov_dd, relativeAltitude, img_width)
            # change UTMx,y to the top left corner (UTM goes as bottom left have the smallest value)
            (img_h,img_w, c) = correctedImage.shape
            x=UTMx-img_w*gsd/2
            y=UTMy+img_h*gsd/2
            # reconsider gsd after warp 
            tfw=(str(gsd*self.refractiveIndex)+'\n0.0000000000\n0.0000000000\n-'+str(gsd*self.refractiveIndex)+'\n'+str(x)+'\n'+str(y))
            file=open(newtfwName,'w')
            file.write(str(tfw)) 
            file.close()  
            print('TFW file created for {}'.format(self.dataMatrix[0]))
            

    def run(self):
        print("\nStarting " + self.name + "\n")
        self.georeferenceImage()
        print("\nExiting " + self.name + "\n")

class Combiner:
    def __init__(self):
        '''
        :param imageList_: List of all images DIR in dataset.
        :param dataMatrix_: Matrix with all pose data in dataset.
        :return:
        '''
        self.imageList = []
        self.tiffList=[]
    
    def performGeoreference(self, dataMatrix_, CRS_, refractiveIndex_):
        self.dataMatrix = dataMatrix_
        self.CRS=CRS_
        self.refractiveIndex=refractiveIndex_
        threads = []
        chunk=10
        length=len(self.dataMatrix)//chunk+1
        j=0
        for j in range(0,length):
            # Create and execute parallel thread for each image
            if (j*chunk+chunk)<len(self.dataMatrix):
                for i in range(j*10,(j*10+chunk)):
                    thread = georeferenceImageThread(i, "Thread-{}".format(i), i, self.dataMatrix[i], self.CRS, self.refractiveIndex)
                    thread.start()
                    threads.append(thread)
                # Wait for all threads to complete
                for t in threads:
                    t.join()
            else: 
                for i in range(j*10,len(self.dataMatrix)):
                    thread = georeferenceImageThread(i, "Thread-{}".format(i), i, self.dataMatrix[i], self.CRS, self.refractiveIndex)
                    thread.start()
                    threads.append(thread)
                # Wait for all threads to complete
                for t in threads:
                    t.join()
            j=j+1

    def createMosaic(self,dataDIR):
        # merge all raster tiffs into one with different compression settings. 
        # Check: https://gis.stackexchange.com/questions/1104/should-gdal-be-set-to-produce-geotiff-files-with-compression-which-algorithm-sh 
        # Check: https://gdal.org/drivers/raster/gtiff.html#creation-options
        input_jpgs=self.dataMatrix[:,0]
        input_tiffs=' '.join([input_jpg.replace('.JPG','.tif').replace("images","outputs") for input_jpg in input_jpgs])
        vrt_dir=Path(dataDIR)/"out.vrt"
        merge_tiff_dir=Path(dataDIR)/"merged.tif"
        gdalvrt=["gdalbuildvrt {} {}/outputs/*.tif".format(vrt_dir,Path(dataDIR))]
        process=subprocess.Popen(gdalvrt, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        output=output.decode(encoding='UTF-8')
        if 'done' in output:
            print("Successfully built vrt")
        else:
            print("built vrt failed, try again")

        cog_tiff_dir=Path(dataDIR)/"merged_cog.tif"
        create_cog=["gdal_translate {} {} -of cog -co BLOCKSIZE=256 -co COMPRESS=LZW -co BIGTIFF=IF_SAFER".format(vrt_dir, cog_tiff_dir)]
        process=subprocess.Popen(create_cog, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        output=output.decode(encoding='UTF-8')
        if 'done' in output:
            print("Successfully created cog")
        else:
            print("Create cog failed, try again")

        # reproj_dir=Path(dataDIR)/"merged_cog_4326.tif"
        # create_cog=["gdalwarp {} {} -t_srs EPSG:4326".format(cog_tiff_dir, reproj_dir)]
        # process=subprocess.Popen(create_cog, stdout=subprocess.PIPE,shell=True)
        # output, error = process.communicate()
        # output=output.decode(encoding='UTF-8')
        # if 'done' in output:
        #     print("Successfully created cog")
        # else:
        #     print("Create cog failed, try again")



        # gdal_merge=["gdal_merge.py -of GTiff -co BIGTIFF=IF_SAFER -co COMPRESS=LZW -co TILED=YES -co BLOCKXSIZE=256 -co BLOCKYSIZE=256 -o {} {}".format(merge_tiff_dir,input_tiffs)]
        # process=subprocess.Popen(gdal_merge, stdout=subprocess.PIPE,shell=True)
        # output, error = process.communicate()
        # output=output.decode(encoding='UTF-8')
        # if 'done' in output:
        #     print("Successfully merged all tiffs")
        # else:
        #     print("Merge failed, try again")
        
        # create_overview=["gdaladdo -r nearest {}".format(merge_tiff_dir)]
        # process=subprocess.Popen(create_overview, stdout=subprocess.PIPE,shell=True)
        # output, error = process.communicate()
        # output=output.decode(encoding='UTF-8')
        # if 'done' in output:
        #     print("Successfully created overviews")
        # else:
        #     print("Create overview failed, try again")
        
        # cog_tiff_dir=Path(dataDIR)/"merged_cog.tif"
        # create_cog=["gdal_translate {} {} -co TILED=YES -co BLOCKSIZE=256 -co COMPRESS=LZW -co BIGTIFF=IF_SAFER -co COPY_SRC_OVERVIEWS=YES".format(merge_tiff_dir, cog_tiff_dir)]
        # process=subprocess.Popen(create_cog, stdout=subprocess.PIPE,shell=True)
        # output, error = process.communicate()
        # output=output.decode(encoding='UTF-8')
        # if 'done' in output:
        #     print("Successfully created cog")
        # else:
        #     print("Create cog failed, try again")
        
        
        
    

