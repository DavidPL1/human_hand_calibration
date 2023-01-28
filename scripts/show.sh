#!/bin/sh

conda activate hand-calibration
python3 src/camera/grab_image.py $1 $2
conda deactivate