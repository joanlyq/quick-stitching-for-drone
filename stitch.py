import exiftool
import glob
from PIL import Image
import utm
from math import tan, radians, atan, degrees, sin, cos, sqrt
from tqdm import tqdm
import numpy as np
import tifffile
import requests

# read image metadata, get roll, pitch, yaw, assuming all nadir, gps coordinate
path = "/Users/yli/Desktop/map/Autel-20220521-FitzroyP3" #"/Users/yli/GeoNadir/mosaic/quick-stitching-for-drone/datasets/images" #
## factor to resize images for quick processing
resize = 8
factor = 1
epsg = 32600
## create list for metadata
img_list = []
gsd_h_list = []
gsd_v_list = []
d_list = []
x_list = []
y_list = []
## extract essential metadata with dji and autel, could expand to other drone images depending on the metadata format
for count, dir in tqdm(enumerate(sorted(glob.glob("{}/images/*.JPG".format(path))))):
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(dir)
        fn = metadata['File:FileName']
        if metadata['EXIF:Make'] == "DJI":
            gimbal_roll = float(metadata['XMP:GimbalRollDegree'])
            gimbal_yaw = float(metadata['XMP:GimbalYawDegree'])
            gimbal_pitch = float(metadata['XMP:GimbalPitchDegree'])
            ## relative altitude is more related to the flight mission planning, different drone or apps may need to revisit this. 
            altitude = float(metadata['XMP:RelativeAltitude'])
            ## flight roll yaw pitch might not be needed due to gyroscope in gimbal should stablize the camera regardless how drone behaves
            flight_roll = float(metadata['XMP:FlightRollDegree'])
            flight_yaw = float(metadata['XMP:FlightYawDegree'])
            flight_pitch = float(metadata['XMP:FlightPitchDegree'])
            im_w = metadata['File:ImageWidth']
            im_h = metadata['File:ImageHeight']
            lat = metadata['Composite:GPSLatitude']
            long = metadata['Composite:GPSLongitude']
            ## metadata fov is usually horizontal FOV, may need to double check
            hfov = metadata['Composite:FOV']
            '''if metadata['EXIF:Model'] == "FC6310":
                if metadata['EXIF:GPSLatitudeRef'] == "N":
                    lat = metadata['EXIF:GPSLatitude']
                else:
                    lat = -metadata['EXIF:GPSLatitude']
                if metadata['EXIF:GPSLongitudeRef'] == "E":
                    long = metadata['EXIF:GPSLongitude']
                else:
                    long = -metadata['EXIF:GPSLongitude']'''
        elif metadata['EXIF:Make'] == "Autel Robotics":
            gimbal_roll = float(metadata['XMP:GimbalRollDegree'])
            gimbal_yaw = float(metadata['XMP:GimbalYawDegree'])
            gimbal_pitch = float(metadata['XMP:GimbalPitchDegree'])
            altitude = float(metadata['XMP:RelativeAltitude'])
            flight_roll = float(metadata['XMP:FlightRollDegree'])
            flight_yaw = float(metadata['XMP:FlightYawDegree'])
            flight_pitch = float(metadata['XMP:FlightPitchDegree'])
            im_w = metadata['File:ImageWidth']
            im_h = metadata['File:ImageHeight']
            lat = metadata['Composite:GPSLatitude']
            long = metadata['Composite:GPSLongitude']
            hfov = metadata['Composite:FOV']
        
        else:
            gimbal_roll = float(metadata['XMP:GimbalRollDegree'])
            gimbal_yaw = float(metadata['XMP:GimbalYawDegree'])
            gimbal_pitch = float(metadata['XMP:GimbalPitchDegree'])
            altitude = float(metadata['XMP:RelativeAltitude'])
            flight_roll = float(metadata['XMP:FlightRollDegree'])
            flight_yaw = float(metadata['XMP:FlightYawDegree'])
            flight_pitch = float(metadata['XMP:FlightPitchDegree'])
            im_w = metadata['File:ImageWidth']
            im_h = metadata['File:ImageHeight']
            lat = metadata['Composite:GPSLatitude']
            long = metadata['Composite:GPSLongitude']
            hfov = metadata['Composite:FOV']

        # calculate vertical FOV from HFOV and image size
        vfov = 2*degrees(atan(tan(radians(hfov*0.5))*im_h/im_w))
        (x,y, utm_band, utm_zone) = utm.from_latlon(lat, long)
        if lat>=0:
            epsg = 32600+utm_band
        else: 
            epsg = 32700+utm_band
        roll = gimbal_roll #+ flight_roll
        yaw = gimbal_yaw
        pitch = gimbal_pitch + 90 #+ flight_pitch
        #gsd = altitude * 2 * tan(radians(hfov * 0.5)) / im_w
        gsd_h = factor*altitude*(tan(radians(hfov*0.5+roll))+tan(radians(hfov*0.5-roll)))/im_w
        gsd_v = factor*altitude*(tan(radians(vfov*0.5+pitch))+tan(radians(vfov*0.5-pitch)))/im_h
        #dtop: gps center to image top, dbottom/dleft/dright
        dleft = altitude*tan(radians(hfov*0.5+roll))
        dright = altitude*tan(radians(hfov*0.5-roll))
        dtop = altitude*tan(radians(vfov*0.5+pitch))
        dbottom = altitude*tan(radians(vfov*0.5-pitch))
        d1 = sqrt(dleft**2+dtop**2)
        d2 = sqrt(dright**2+dtop**2)
        d3 = sqrt(dright**2+dbottom**2)
        d4 = sqrt(dleft**2+dbottom**2)
        d = max([d1,d2,d3,d4])
        #metadata_list = [dir, fn, lat, long, x, y, gsd]
        #df.loc[len(df)] = metadata_list
        
        dict = {}
        dict['fn'] = fn
        dict['dir'] = dir 
        dict['lat'] = lat 
        dict['altitude'] = altitude
        dict['long'] = long
        dict['roll'] = roll
        dict['pitch'] = pitch
        dict['yaw'] = yaw
        dict['hfov'] = hfov
        dict['vfov'] = vfov
        dict['x'] = x 
        dict['y'] = y
        dict['gsd_h'] = gsd_h 
        dict['gsd_v'] = gsd_v 
        gsd_h_list.append(gsd_h)
        gsd_v_list.append(gsd_v)
        x_list.append(x)
        y_list.append(y)
        d_list.append(d)
        img_list.append(dict)
        

            # undistort
                # read lens distortion file to get the camera matrix and distortion coefficient
                # use opencv to undistort the image

        # rotate image and fill the rest with null or 0

## calculate average gsd both horizontally and vertically of all images
ave_gsd_h = sum(gsd_h_list)/len(gsd_h_list)*resize
ave_gsd_v = sum(gsd_v_list)/len(gsd_v_list)*resize
xmax = max(x_list)
xmin = min(x_list)
ymax = max(y_list)
ymin = min(y_list)
dmax = max(d_list)
dx = xmax-xmin + 2*dmax
dy = ymax-ymin + 2*dmax
total_w = int(dx/ave_gsd_h)
total_h = int(dy/ave_gsd_v)
## create blank canvas using the max possible width and height
new_im = Image.new('RGBA', (total_w, total_h))

def getWKT_PRJ (epsg_code):
    # access projection information
    wkt = requests.get("http://spatialreference.org/ref/epsg/{}/prettywkt/".format(epsg_code))
    # remove spaces between charachters
    remove_spaces = wkt.text.replace(" ","")
    # place all the text on one line
    output = remove_spaces.replace("\n", "")
    return output

def find_coeffs(pa, pb):
    #where pb is the four vertices in the current plane, and pa contains four vertices in the resulting plane.
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = np.matrix(matrix, dtype=float)
    B = np.array(pb).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

def get_alpha(im_w, im_h):

    third_w = int(im_w/2)
    third_h = int(im_h/2)

    left_grad = np.linspace(1, 255, third_w)
    middle_length = im_w - (third_w * 2)
    middle_section = np.full(middle_length, 255)
    right_grad = np.flip(left_grad)
    horiz_vec = np.append(np.append(left_grad, middle_section), right_grad)
    horiz_mat = np.tile(horiz_vec, (im_h, 1))

    top_grad = np.linspace(1, 255, third_h)
    middle_length = im_h - (third_h * 2)
    middle_section = np.full(middle_length, 255)
    bottom_grad = np.flip(top_grad)
    vert_vec = np.append(np.append(top_grad, middle_section), bottom_grad)
    vert_mat = np.tile(vert_vec, (im_w, 1)).T

    combined_mat = np.minimum(horiz_mat, vert_mat)

    return Image.fromarray(np.uint8(combined_mat))

def rotate(pt, angle, origin):
    (x, y) = pt
    offset_x, offset_y = origin
    adjusted_x = (x - offset_x)
    adjusted_y = (y - offset_y)
    cos_rad = cos(radians(angle))
    sin_rad = sin(radians(angle))
    dy = cos_rad * adjusted_x - sin_rad * adjusted_y
    dx = sin_rad * adjusted_x + cos_rad * adjusted_y
    return dx, dy

def get_point_coord(original_img, pt, angle, rotated_img):
    w, h = original_img.size
    origin = (w/2, h/2)
    dx, dy = rotate(pt, angle, origin)
    w_new, h_new = rotated_img.size
    xoffset, yoffset = w_new/2, h_new/2
    x_new, y_new = dx+xoffset, dy+yoffset
    return x_new, y_new

def rotate_image(img,angle):
    rotated_img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    return rotated_img

def transform_img(img,im_w, im_h, pa, pb):
    coeffs = find_coeffs(pa, pb)
    transformed_img = img.transform((im_w, im_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    return transformed_img

for i in tqdm(img_list): 
    dir = i['dir']  
    altitude = i['altitude']
    yaw = i['yaw']
    pitch = i['pitch']
    roll = i['roll']
    hfov = i['hfov']
    vfov = i['vfov']
    gsd_h = i['gsd_h']
    gsd_v = i['gsd_v']
    x = i['x']
    y = i['y']
    if yaw>0:
        angle = 360-yaw
    else:
        angle = -yaw
    img = Image.open(dir).convert('RGBA')
    im_w, im_h = img.size
    alpha = get_alpha(im_w, im_h)
    img.putalpha(alpha)
    hscale = gsd_h/ave_gsd_h
    vscale = gsd_v/ave_gsd_v
    img = img.resize((round(hscale*im_w),round(vscale*im_h)))
    im_w, im_h = img.size
    ## transform according to pitch and roll
    xb = im_w
    yb = im_h
    pb = [(0,0),(0,yb), (xb,0), (xb,yb)]
    xa = round(xb/(2*tan(radians(hfov*0.5)))*(tan(radians(hfov*0.5+roll))+tan(radians(hfov*0.5-roll))))
    ya = round(yb/(2*tan(radians(vfov*0.5)))*(tan(radians(vfov*0.5+pitch))+tan(radians(vfov*0.5-pitch))))
    if pitch > 0: 
        ytop = yb-ya
        ybottom = yb
    else: 
        ytop = 0
        ybottom = ya
    if roll > 0:
        xleft = xb-xa
        xright = xb
    else:
        xleft = 0
        xright = xa 
    pa = [(xleft, ytop), (xleft, ybottom), (xright, ytop), (xright, ybottom)]
    #img.show()
    img = transform_img(img, xa, ya, pa, pb)
    #img.show()
    
    dleft = round(xa*tan(radians(hfov*0.5+roll))/(tan(radians(hfov*0.5+roll))+tan(radians(hfov*0.5-roll))))
    dtop = round(ya*tan(radians(vfov*0.5+pitch))/(tan(radians(vfov*0.5+pitch))+tan(radians(vfov*0.5-pitch))))
    gps_paper_coord = (dleft,dtop)
    
    rotated_img = rotate_image(img,angle)
    #rotated_img.show()
    new_px, new_py = get_point_coord(img, gps_paper_coord, angle, rotated_img)    
    left = x - new_px*ave_gsd_h
    top = y + new_py*ave_gsd_v
    left_paper = round((x-xmin)/ave_gsd_h)
    top_paper = round((ymax-y)/ave_gsd_v)
    new_im.paste(rotated_img,(left_paper,top_paper), rotated_img)

new_im.show()
worldfile = open("{}output.tfw".format(path), "w")  
worldfile.write(str(ave_gsd_h)+"\n")
worldfile.write(str(0)+"\n") # generally = 0
worldfile.write(str(0)+"\n") # generally = 0
worldfile.write(str(-ave_gsd_v)+"\n")
worldfile.write(str(xmin)+"\n")
worldfile.write(str(ymax)+"\n")
worldfile.close()

# create the .prj file
prj = open("{}output.prj".format(path), "w")
try: 
    epsg = getWKT_PRJ (epsg)
    prj.write(epsg)
    prj.close()
except:
    print("failed to generate .prj file")
    pass

new_im.save("{}output.tif".format(path), compression='lzw')
# tifffile.imsave('/Users/yli/GeoNadir/output2.tif', new_im, compression='LZW') 
# rotate image and fill the rest with null or 0
# copy paste on to a blank canvas
# read second image, undistort, rotate
# combine with the first image, recenter the image coordinate
print("DONE")