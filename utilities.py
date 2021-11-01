import cv2
import numpy as np

def get_sec(ts):
    """Get Seconds from time."""
    secs= sum(int(x) * 60 ** i for i, x in enumerate(reversed(ts.split(':'))))
    return secs

def dms_to_dd(dms):
    dd = int(dms[0]) + int(dms[2])/60 + float(dms[3])/3600
    return dd

def importData(exif_info):
    '''
    :param exif_info: direct bash cmd output of images metadata using "exiftool", can be a directory of a txt file with all the exifformat
    :return: dataMatrix: A NumPy ndArray contaning all of the exif data (incouding pose in YPR form). 
        fileDIRMatrix: A Python List of NumPy ndArrays containing images.
    '''

    allImages = [] #list of cv::Mat aimghes
    dataMatrix = np.genfromtxt(exif_info,delimiter=",", usecols=range(1,9),skip_header=1,dtype=str)
    '''createDateMatrix = np.genfromtxt(fileName,delimiter=",",usecols=[8],skip_header=1,dtype=str)
    createTime=[]
    for i in range(0,createDateMatrix.shape[0]):
        ts=str(createDateMatrix[i]).split(" ")[1]
        createTime.append(get_sec(ts))
    createTime_array=np.asarray(createTime)'''
    # obtain ave altitude in meter and FOV in decimal degree
    # check new drone for FOV and HFOV
    # FOV, HFOV DJI P4P explanation https://phantompilots.com/threads/p4p-lens-field-of-view.114160/
    fileDIRMatrix = np.genfromtxt(exif_info,delimiter=",",usecols=[0], skip_header=1, dtype=str) #read filen name strings
    return fileDIRMatrix, dataMatrix

def display(title, image):
    '''
    OpenCV machinery for showing an image until the user presses a key.
    :param title: Window title in string form
    :param image: ndArray containing image to show
    :return:
    '''

    cv2.namedWindow(title,cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title,1920,1080)
    cv2.imshow(title,image)
    cv2.waitKey(400)
    cv2.destroyWindow(title)

def drawMatches(img1, kp1, img2, kp2, matches):
    """
    Makes an image with matched features denoted.
    drawMatches() is missing in OpenCV 2. This boilerplate implementation taken from http://stackoverflow.com/questions/20259025/module-object-has-no-attribute-drawmatches-opencv-python
    """

    # Create a new output image that concatenates the two images together
    # (a.k.a) a montage
    rows1 = img1.shape[0]
    cols1 = img1.shape[1]
    rows2 = img2.shape[0]
    cols2 = img2.shape[1]

    out = np.zeros((max([rows1,rows2]),cols1+cols2,3), dtype='uint8')

    # Place the first image to the left
    out[:rows1,:cols1] = np.dstack([img1, img1, img1])

    # Place the next image to the right of it
    out[:rows2,cols1:] = np.dstack([img2, img2, img2])

    # For each pair of points we have between both images
    # draw circles, then connect a line between them
    for m in matches:

        # Get the matching keypoints for each of the images
        img1_idx = m.queryIdx
        img2_idx = m.trainIdx

        # x - columns
        # y - rows
        (x1,y1) = kp1[img1_idx].pt
        (x2,y2) = kp2[img2_idx].pt

        # Draw a small circle at both co-ordinates
        radius = 8
        thickness = 3
        color = (255,0,0) #blue
        cv2.circle(out, (int(x1),int(y1)), radius, color, thickness)
        cv2.circle(out, (int(x2)+cols1,int(y2)), radius, color, thickness)

        # Draw a line in between the two points
        cv2.line(out, (int(x1),int(y1)), (int(x2)+cols1,int(y2)), color, thickness)

    # Also return the image if you'd like a copy
    return out