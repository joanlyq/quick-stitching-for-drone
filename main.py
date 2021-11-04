import utilities as util
import mosaic as mosaic
import geometry as gm
import os
from pathlib import Path
import numpy as np
import subprocess
import argparse
import exiftool
import glob
import timing
#dataDIR = "/Users/yli/GeoNadir/mosaic/overlay_drone_footprint/datasets"
from time import time

def parse_args():
    parser = argparse.ArgumentParser(description='Mosaic drone images for without orthorectify')
    parser.add_argument("--DATA_DIR", default='/Users/yli/GeoNadir/mosaic/quick-stitching-for-drone/datasets', help='Directory of images to be processed')
    parser.add_argument("--CRS", default='EPSG:7855', help='coordinate reference system for quick display in qgis')
    args = parser.parse_args()
    return args.DATA_DIR, args.CRS

if __name__ == '__main__':
    # Parse command line arguments
    (DATA_DIR,CRS) = parse_args()
    exif_dir=Path(DATA_DIR)/"exif_info.txt"
    img_dir=Path(DATA_DIR)/"images"
    output_dir=Path(DATA_DIR)/"outputs"
    exifMatrix = []

    #fileName = Path("/Users/yli/GeoNadir/mosaic/overlay_drone_footprint/datasets/imageData.txt")
    if exif_dir.exists():
        exif_output=open(exif_dir).readlines()
        if len(exif_output) == len(os.listdir(img_dir)):
            print("read exif_info.txt")
        else: 
            for img in img_dir.glob('*.JPG'):
                for (k,v) in Image.open(img._getexif().items()):
                    print('%s = %s' % (TAGS.get(k), v))
            bashcmd = ["exiftool -csv -filename -gpslatitude -gpslongitude -FlightYawDegree -FlightPitchDegree -FlightRollDegree -relativeAltitude -fov {} > {}".format(img_dir, exif_dir)]
            process = subprocess.Popen(bashcmd, stdout=subprocess.PIPE,shell=True)
            output, error = process.communicate()
            exif_output=open(exif_dir).readlines()
            # exif_output=output.decode("utf-8").splitlines()
            print("finish extracting exif info")
    else: 
        tags= ["filename", "gpslatitude", "gpslongitude","FlightYawDegree", "FlightPitchDegree", "FlightRollDegree", "relativeAltitude", "fov"]
        #img_ls=[str(img) for img in img_dir.glob('*.JPG')]
        for img in sorted(img_dir.glob('*.JPG')):
            with exiftool.ExifTool() as et:
                exif_all=et.get_metadata(str(img))
                exif_info = np.array(list(et.get_tags(tags,str(img)).values()))
                exifMatrix.append(exif_info)
                #exif_output = et.get_tags(tags,img)

        '''bashcmd = ["exiftool -csv -filename -gpslatitude -gpslongitude -FlightYawDegree -FlightPitchDegree -FlightRollDegree -relativeAltitude -fov {} > {}".format(img_dir, exif_dir)]
        process = subprocess.Popen(bashcmd, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        exif_output=open(exif_dir).readlines()
        # exif_output=output.decode("utf-8").splitlines()
        print("finish extracting exif info")'''
    timing.log("extract exif", elapsed=time())

    try:
        os.makedirs(output_dir)
    except FileExistsError:
    # directory already exists
        pass
    timing.log("create output dir", elapsed=time())

    dataMatrix = util.importData(exifMatrix)
    myCombiner = mosaic.Combiner(dataMatrix, CRS)
    result = myCombiner.createMosaic(DATA_DIR)
    print("MOSAIC DONE!")

