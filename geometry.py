import numpy as np
import cv2
import math as m
try:
    from osgeo import gdal, osr
except ImportError:
    import gdal, osr

def computeUnRotMatrix(pose):
    '''
    See http://planning.cs.uiuc.edu/node102.html. Undoes the rotation of the craft relative to the world frame.
    :param pose: A 1x6 NumPy ndArray containing pose information in [img_fname,GPS_lat,GPS_lon,Y,P,R,relativeAltitude,FOV] format
    :return: A 3x3 rotation matrix that removes perspective distortion from the image to which it is applied.
    '''
    a = float(pose[0])*np.pi/180 #alpha
    b = float(pose[1])*np.pi/180 #beta
    g = float(pose[2])*np.pi/180 #gamma
    #Compute R matrix according to source.
    Rz = np.array(([m.cos(a), -1*m.sin(a),    0],
                   [m.sin(a),    m.cos(a),    0],
                   [       0,           0,     1]))

    Ry = np.array(([ m.cos(b),           0,     m.sin(b)],
                   [        0,           1,            0],
                   [-1*m.sin(b),           0,     m.cos(b)]))

    Rx = np.array(([        1,           0,            0],
                   [        0,    m.cos(g),  -1*m.sin(g)],
                   [        0,    m.sin(g),     m.cos(g)]))
    Ryx = np.dot(Rx,Ry)
    R = np.dot(Rz,Ryx) #Care to perform rotations in roll, pitch, yaw order.
    R[0,2] = 0
    R[1,2] = 0
    R[2,2] = 1
    Rtrans = R.transpose()
    InvR = np.linalg.inv(Rtrans)
    #Return inverse of R matrix so that when applied, the transformation undoes R.
    return InvR

def warpPerspectiveWithPadding(image,transformation): #Make it without padding
    '''
    When we warp an image, its corners may be outside of the bounds of the original image. This function creates a new image that ensures this won't happen.
    :param image: ndArray image
    :param transformation: 3x3 ndArray representing perspective trransformation
    :param kp: keypoints associated with image
    :return: transformed image
    '''

    height = image.shape[0]
    width = image.shape[1]
    corners = np.float32([[0,0],[0,height],[width,height],[width,0]]).reshape(-1,1,2) #original corner locations

    warpedCorners = cv2.perspectiveTransform(corners, transformation) #warped corner locations
    [xMin, yMin] = np.int32(warpedCorners.min(axis=0).ravel() - 0.5) #new dimensions
    [xMax, yMax] = np.int32(warpedCorners.max(axis=0).ravel() + 0.5)
    translation = np.array(([1,0,-1*xMin],[0,1,-1*yMin],[0,0,1])) #must translate image so that all of it is visible
    fullTransformation = np.dot(translation,transformation) #compose warp and translation in correct order
    result = cv2.warpPerspective(image, fullTransformation, (xMax-xMin, yMax-yMin),cv2.BORDER_TRANSPARENT)
    return result

def get_gsd(FOV_dd,altitude,img_width):
    gsd= (m.tan(FOV_dd* m.pi /360))*altitude/(img_width/2)
    return gsd

def array2raster(newRasterfn,UTMx, UTMy,GSD, CRS, array):

    cols = array.shape[1]
    rows = array.shape[0]
    bands = array.shape[2]
    originX = UTMx
    originY = UTMy

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, bands, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, GSD, 0, originY, 0, GSD))
    outband = outRaster.GetRasterBand(bands)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(CRS)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()