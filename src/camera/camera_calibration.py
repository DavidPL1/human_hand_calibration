import cv2
import numpy as np
import os
import argparse

from grab_image import grab_image


### PUBLIC FUNCTIONS ###

def load_camera_params():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../calibration.npy')
    with open(filename, 'rb') as f:
        camera_matrix = np.load(f)
        distortion_coeff = np.load(f)
        corners = np.load(f)
        board_size = np.load(f)
        corner_size = np.load(f)
    return camera_matrix, distortion_coeff, corners, (board_size[0], board_size[1]), corner_size

# Shows distorted images at a given path
def load_distorted_image(path, show=False):
    image = grab_image(path, cvt_color=True)
    if show:
        cv2.imshow('Distorted Image', image)
        cv2.waitKey(0)
    return image


### PRIVATE FUNCTIONS ###

# Detects checkerboard corners and returns their corresponding 2D image and 3D world points
def __getCheckerboardPoints(image, checkerboard_size, display=False):
    board_columns, board_rows = checkerboard_size

    # Prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    grid_points = np.zeros((board_rows*board_columns,3), np.float32)
    grid_points[:,:2] = np.mgrid[0:board_columns,0:board_rows].T.reshape(-1,2)

    # Arrays to store 3D world points and 2D image points from all the images.
    world_points = [] # 3d points in real world space
    image_points = [] # 2d points in image plane.

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(image, (board_columns,board_rows), None)

    # Continue if previous operation was successful
    if ret == True:
        world_points.append(grid_points)
        # Increase corner accuracy with function cv2.cornerSubPix()
        corners_refined = cv2.cornerSubPix(image, corners, (11,11), (-1,-1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
        image_points.append(corners_refined)
        # Draw and display the corners if display was set to true 
        if display == True:
            image = cv2.drawChessboardCorners(image, (board_columns,board_rows), corners_refined,ret)
            cv2.imshow('img', image)
            cv2.waitKey(0)
    else:
        print('Could not detect checkerboard corners')

    cv2.destroyAllWindows()
    image_size = image.shape[::-1]

    return world_points, image_points, image_size

# Undistorts a given image and returns the undistoted image, 
# the camera matrix, the distortion coefficients, the rotation vectors 
# and the translation vectors
def __calibrate(image, world_points, image_points, image_size):
    _, camera_matrix, distortion_coeff, rotation_vecs, translation_vecs = cv2.calibrateCamera(world_points, image_points, image_size, None, None)
    height, width = image.shape[:2]
    size = (width, height)
    # Get optimal new camera matrix
    camera_matrix_opt, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coeff, size, 1, size)
    # undistort image
    image_undistorted = cv2.undistort(image, camera_matrix, distortion_coeff, None, camera_matrix_opt)
    return image_undistorted, camera_matrix, distortion_coeff, rotation_vecs, translation_vecs

def __save_camera_params(camera_matrix, distortion_coeff, corners, board_size, corner_size):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../calibration.npy')
    with open(filename, 'wb') as f:
        np.save(f, camera_matrix)
        np.save(f, distortion_coeff)
        np.save(f, corners)
        w, h = board_size
        np.save(f, np.array([w, h]))
        np.save(f, np.array([corner_size]))


### MAIN FUNCTION ###
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--device', type=int, help="Camera device number (defaults to 0)", default=0)
    parser.add_argument('-W', '--width', type=int, help="Width of chessboard (number of squares) (defaults to 7)", default=7)
    parser.add_argument('-H', '--height', type=int, help="Height of chessboard (number of squares) (defaults to 9)", default=9)
    parser.add_argument('-L', '--corner_length', type=float, help="Height of chessboard (number of squares) (defaults to 9)", default=0.22)
    args = parser.parse_args()

    print('Load Image')
    image = load_distorted_image(args.device, show=True)
    print('Determine Checkerboard Points')
    wp, ip, size = __getCheckerboardPoints(image, (args.width, args.height), display=True)
    print('Calibrate')
    im, cmatrix, distcoeff, rvecs, tvecs = __calibrate(image, wp, ip, size)
    __save_camera_params(cmatrix, distcoeff, ip, (args.width, args.height), args.corner_length)
    print('Calibration saved')
