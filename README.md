# Hand Calibration

## Setup
We provide scripts for Linux/MacOS (\*.sh) and Windows (\*.bat). Use the ones according to your OS.
1. Set up camera rig and place chessboard
2. Install given conda environment using `conda env create -f environment.yaml`
3. Calibrate the camera using `scripts/calibrate_camera.sh --device <camera_index> --width <width> --height <height> --corner_length <corner_length>`
   * camera_index: webcam has index 0, additional cameras have indices 1, 2, ...
   * width: width of the calibration chessboard
   * height: height of the calibration chessboard
   * corner_length: distance between squares of chessboard pattern

Every time the camera setup changes you need to perform the calibration again. If the setup persists, you don't need to calibrate again. The calibration is saved in file `calibration.npy`.

## Execute
1. Place hand on top of camera rig
2. Execute the hand calibration using `scripts/execute.sh --device <camera_index> --calibration <path_to_calibration_file>` (alternatively use `--image <image_path>` instead of `--device` to load an image file)
   * Follow instructions
   * Presse Q to quit

## Test
You can also test this tool using script `scripts/show.sh` to view a camera image or script `scripts/test_distance.sh` to test the distance estimation.

## Dev instructions
### Distance Estimation

``` python
from src.camera.distance_estimation import estimate_distance 

point_a = ...
point_b = ...
distance = estimate_distance(point_a, point_b)
```

### Grab Image
``` python
from src.camera.grab_image import grab_image 

image = grab_image(camera_index)
```
