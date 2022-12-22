import cv2
import os
import camera_calibration as camera_calibration
import argparse


def grab_image(camera_idx):
    camera = cv2.VideoCapture(camera_idx)
    for _ in range(30):
        ok, image = camera.read()

    if not ok:
        print('Could not grab image')
    camera.release()
    return image


### MAIN FUNCTION ###
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', type=int, help="Camera device number (defaults to 0)", default=0)
    args = parser.parse_args()

    # read image
    image = grab_image(args.device)

    # show image
    cv2.imshow('Image', image)
    cv2.waitKey(0)

    # save image
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../image_grab.png')
    cv2.imwrite(filename, image)
