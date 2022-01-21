from osgeo import gdal
import argparse

# Shift raster geotiff orthomosaic by given x,y coordinates in metres within coordinate frame of the raster
# Usage:
# shift_raster.py --ortho_file <string.tif> --x <float> --y <float>


def parse_args():
    parser = argparse.ArgumentParser(description='Shift raster ortho by given x/y.')
    parser.add_argument("--ortho_file", default="", help="Ortho file .tif")
    parser.add_argument("--x", default="", help="Float to shift x by")
    parser.add_argument("--y", default="", help="Float to shift y by")
    args = parser.parse_args()
    return args.ortho_file, args.x, args.y

def shift_raster(ortho_file, x, y):

    # Check for tif
    if not ortho_file.endswith('.tif'):
        print("Error: You must provide a TIF image file.")

    # Register GDAL
    gdal.AllRegister()

    # Open in read/write mode
    rast_src = gdal.Open(ortho_file, 1)

    # Get affine transform coefficients
    gt = rast_src.GetGeoTransform()

    # Convert tuple to list, so we can modify it
    gtl = list(gt)
    gtl[0] += x  # +: east, -: west
    gtl[3] += y  # +:north, -: south

    # Save the geotransform to the raster
    rast_src.SetGeoTransform(tuple(gtl))
    rast_src = None # equivalent to save/close

if __name__ == '__main__':
    # Parse command line arguments
    (ortho_file, x, y) = parse_args()
    shift_raster(ortho_file, float(x), float(y))

