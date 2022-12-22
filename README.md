# Hand Calibration

## Steps
1. Set up camera rig and place chessboard
2. Calibrate the camera using `scripts/calibrate_camera.sh --device <camera_index> --width <width> --height <height> --corner_length <corner_length>`
   * camera_index: webcam has index 0, additional cameras have indices 1, 2, ...
   * width: width of the calibration chessboard
   * height: height of the calibration chessboard
   * corner_length: distance between squares of chessboard pattern
3. Remove chessboard
5. Place hand on top of camera rig
4. Execute the hand calibration using `scripts/execute.sh --device <camera_index>` 
   * Follow instructions
   * Presse Q to quit

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