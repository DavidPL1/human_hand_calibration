import numpy as np
import cv2
import math
import camera_calibration as camera_calibration
from functools import partial
import argparse
import numpy as np
import os
import sys


### PUBLIC FUNCTIONS ###

def estimate_distance(a, b, calib_path, simple=False):
    camera_matrix, dist_coeff, corners, board_size, corner_size = camera_calibration.load_camera_params(calib_path=calib_path)
    if simple:
        return __estimateDistanceSimple([a, b], corners, board_size, corner_size)
    else:
        return __estimateDistance([a, b], camera_matrix, dist_coeff, corners, board_size, corner_size)

def get_palm_axis_offset_euclidian(ref, palm, other):
    p1 = np.array(ref)
    p2 = np.array(palm)
    p3 = np.array(other)

    r = project_point_on_line(p1, p2, p3)

    try:
        x = int(p3[0] - r[0])
        y = int(r[1] -  p2[1])
    except ValueError:
        print(f"p1: {p1}, p2: {p2}, r: {r}")

    return x, y

# Projects point p onto line ab
def project_point_on_line(a, b, p):
    return a + np.dot(p-a, b-a) / np.dot(b-a, b-a) * (b-a)

### PRIVATE FUNCTIONS ###

# imshow mouse event
def __getPointCoordEvent( image, event_points, event,x,y,flags,param):
    if event == cv2.EVENT_FLAG_LBUTTON:
        if(len(event_points) < 2):
            event_points.append([x,y])
            cv2.circle(image, (x,y), 3, (0, 0, 255), thickness=3)
            cv2.imshow("Distance Estimation", image)     

# Project image point to world point
def __pointToWorld(image_point, camera_matrix, rotation_matrix, translation_vector):
    # image point as (x,y,1)
    ip = np.ones((3,1))
    ip[0,0] = image_point[0]
    ip[1,0] = image_point[1]
    ip = np.asmatrix(ip)
    # assumption: z-coordinate = 0
    z = 0
    # invert camera and rotation matrix
    r_inv = np.asmatrix(np.linalg.inv(rotation_matrix))
    c_inv = np.asmatrix(np.linalg.inv(camera_matrix))
    # solve equation:
    # s * imagePoint = CameraMatrix * ( RotationMatrix * worldPoint + TranslationVector )
    # for worldPoint
    tempMat = r_inv * c_inv * ip
    tempMat2 = r_inv * translation_vector
    s = (z + tempMat2[2,0]) / tempMat[2,0]
    worldPoint = s*tempMat - tempMat2
    return worldPoint

# Estimates the distance between two point. Assumes that the camera is parallel to the checkerboard
def __estimateDistanceSimple(points, corners, board_size, corner_size):
    columns, rows = board_size
    corners = corners[0]

    # Calculate mean distance between corner points
    total = 0
    for i in range(rows):
        for j in range(columns-1):
            total += __euclideanDistance(corners[(i*columns)+j][0], corners[(i*columns)+j+1][0])
    mean = total / (rows*(columns-1))
    # Calculate estimated distance
    measurePointDistance = __euclideanDistance(points[0], points[1])
    return corner_size * measurePointDistance / mean

# Estimates the distance between two point. There is no assumption regarding the camera position
def __estimateDistance(points, camera_matrix, distortion_coeff, corners, board_size, corner_size):
    corners = corners[0]
    # Get known world points of the checkerboard corners
    boardColumns, boardRows = board_size
    board_points_3D = np.zeros((boardRows*boardColumns,3), np.float32)
    board_points_3D[:,:2] = np.mgrid[0:boardColumns,0:boardRows].T.reshape(-1,2)
    board_points_3D = board_points_3D * corner_size

    # Calculate rotation and translation vector
    _, rVec, tVec = cv2.solvePnP(board_points_3D, corners, camera_matrix, distortion_coeff)
    # Calculate rotation matrix
    r, _ = cv2.Rodrigues(rVec)
    # Points to world points
    p1 = __pointToWorld(points[0], camera_matrix, r, tVec)
    p2 = __pointToWorld(points[1], camera_matrix, r, tVec)
    # Calculate euclidean distance
    distance = __euclideanDistance(p1, p2)
    return distance

# Returns the euclidean distance of two points
def __euclideanDistance(p1, p2):
    return math.sqrt( (p1[0]-p2[0])**2+(p1[1]-p2[1])**2 )

### MAIN FUNCTION

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    default_calib = os.path.normpath(os.path.join(dirname, os.pardir, 'calibration.npy'))

    parser = argparse.ArgumentParser()
    
    ex_group = parser.add_mutually_exclusive_group()
    ex_group.add_argument('-d', '--device', type=int, help="Camera device number (defaults to 0)", default=0)
    ex_group.add_argument('-i', '--image', help="Path to image to load")
    parser.add_argument('-c', '--calibration', type=str, help=f"Path to camera calibration (defaults to {default_calib})", default=default_calib)
    args = parser.parse_args()

    if not os.path.isfile(args.calibration):
        print(f'[FATAL ERROR]: calibration file "{args.calibration}" does not exists or is not a file!')
        sys.exit(-1)

    # Choose points for distance estimation -> mouse event
    if args.image:
        image = cv2.imread(args.image)
    else:
        image = camera_calibration.load_distorted_image(args.device, show=False)

    points = []
    cv2.imshow("Distance Estimation", image)
    cv2.setMouseCallback("Distance Estimation", partial(__getPointCoordEvent, image, points))
    cv2.waitKey(0)

    print("Simple distance estimation:", estimate_distance(points[0], points[1], args.calibration, simple=True))
    print("Distance estimation:", estimate_distance(points[0], points[1], args.calibration))

