@echo off
setlocal

SET scriptpath=%dp0

call activate hand-calibration
python %scriptpath%\..\src\camera\grab_image.py %1 %2
call conda deactivate