import utilities as util
import mosaic as mosaic
import geometry as gm
# import os
from pathlib import Path
import numpy as np
import subprocess
import argparse
from PIL import Image
from PIL.ExifTags import TAGS

#dataDIR = "/Users/yli/GeoNadir/mosaic/overlay_drone_footprint/datasets"


def parse_args():
    parser = argparse.ArgumentParser(description='Mosaic drone images for without orthorectify')
    parser.add_argument("--DATA_DIR", default='/Users/yli/GeoNadir/mosaic/overlay_drone_footprint/datasets', help='Directory of images to be processed')
    parser.add_argument("--CRS", default='EPSG:7855', help='coordinate reference system for quick display in qgis')
    args = parser.parse_args()
    return args.DATA_DIR, args.CRS

if __name__ == '__main__':
    # Parse command line arguments
    (DATA_DIR,CRS) = parse_args()
    exif_dir=Path(DATA_DIR)/"exif_info.txt"
    print(type(DATA_DIR))
    print(exif_dir.exists())
    img_dir=Path(DATA_DIR)/"images"
    output_dir=Path(DATA_DIR)/"outputs"
    
    #fileName = Path("/Users/yli/GeoNadir/mosaic/overlay_drone_footprint/datasets/imageData.txt")
    if exif_dir.exists():
        exif_output=open(exif_dir).readlines()
        if len(exif_output) == len(os.listdir(img_dir)):
            print("read exif_info.txt")
        else: 
            bashcmd = ["exiftool(-k).exe -csv -filename -gpslatitude -gpslongitude -FlightYawDegree -FlightPitchDegree -FlightRollDegree -relativeAltitude -fov {}*.JPG > {}".format(img_dir, exif_dir)]
            process = subprocess.Popen(bashcmd, stdout=subprocess.PIPE,shell=True)
            output, error = process.communicate()
            exif_output=open(exif_dir).readlines()
            # exif_output=output.decode("utf-8").splitlines()
            print("finish extracting exif info")
    else: 
        bashcmd = ["exiftool(-k).exe -csv -filename -gpslatitude -gpslongitude -FlightYawDegree -FlightPitchDegree -FlightRollDegree -relativeAltitude -fov {}*.JPG > {}".format(img_dir, exif_dir)]
        process = subprocess.Popen(bashcmd, stdout=subprocess.PIPE,shell=True)
        output, error = process.communicate()
        exif_output=open(exif_dir).readlines()
        # exif_output=output.decode("utf-8").splitlines()
        print("finish extracting exif info")
    
    try:
        os.makedirs(output_dir)
    except FileExistsError:
    # directory already exists
        pass

    fileDIRMatrix, dataMatrix = util.importData(exif_output)
    myCombiner = mosaic.Combiner(fileDIRMatrix, dataMatrix, CRS)
    result = myCombiner.createMosaic(DATA_DIR)
    print("MOSAIC DONE!")

