#!/bin/sh

conda activate hand-calibration
python3 src/camera/camera_calibration.py $1 $2 $3 $4 $5 $6 $7 $8
conda deactivate