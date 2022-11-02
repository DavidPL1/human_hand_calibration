# Hand Calibration

## Camera Calibration 
1. Find out the camera index and adapt `PATH_TO_VIDEO` in `src/camera/camera_calibration`
2. Execute `scripts/calibrate.sh` to generate a calibration file `calibration.npy` later used for the distance estimation

## Distance Estimation

``` python
from src.camera.distance_estimation import estimate_distance 

point_a = ...
point_b = ...
distance = estimate_distance(point_a, point_b)
```

## Grab Image
``` python
from src.camera.grab_image import grab_image 
from src.camera.distance_estimation import PATH_TO_VIDEO 

image = grab_image(PATH_TO_VIDEO)
```