@echo off
setlocal

SET scriptpath=%dp0

call activate hand-calibration
python %scriptpath%\..\src\camera\camera_calibration.py %1 %2 %3 %4 %5 %6 %7 %8
call conda deactivate