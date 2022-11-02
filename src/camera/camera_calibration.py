import cv2
import numpy as np
import os


### CONSTANTS ###
CHECKERBOARD_SIZE = (7, 9)
PATH_TO_VIDEO = '/Users/tmarkmann/Downloads/checkerboard.mov'


### PUBLIC FUNCTIONS ###

def load_camera_params():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../calibration.npy')
    with open(filename, 'rb') as f:
        camera_matrix = np.load(f)
        distortion_coeff = np.load(f)
        corners = np.load(f)
    return camera_matrix, distortion_coeff, corners

# Shows distorted images at a given path
def load_distorted_image(path, show=False):
    image = __videoRead(path)
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

def __save_camera_params(camera_matrix, distortion_coeff, corners):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../calibration.npy')
    with open(filename, 'wb') as f:
        np.save(f, camera_matrix)
        np.save(f, distortion_coeff)
        np.save(f, corners)

def __videoRead(path):
    video_file = cv2.VideoCapture(path)
    ok, frame = video_file.read()
    if not ok:
        print('Could not grab image')
        exit(1)
    video_file.release()
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


### MAIN FUNCTION ###
if __name__ == "__main__":
    image = load_distorted_image(PATH_TO_VIDEO, show=False)
    wp, ip, size = __getCheckerboardPoints(image, CHECKERBOARD_SIZE, display=True)
    im, cmatrix, distcoeff, rvecs, tvecs = __calibrate(image, wp, ip, size)
    __save_camera_params(cmatrix, distcoeff, ip)
    print('Calibration saved')
