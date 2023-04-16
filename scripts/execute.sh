#!/bin/sh

conda activate hand-calibration
python3 src/camera/keypoint_gui.py $1 $2 $3 $4
conda deactivate