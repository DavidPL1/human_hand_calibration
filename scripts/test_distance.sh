#!/bin/sh

conda activate hand-calibration
python3 src/camera/distance_estimation.py $1 $2
conda deactivate