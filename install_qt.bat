@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "C:\projects\0.ongoing\rings\tools\vcpkg"
vcpkg install qt taglib --triplet x64-windows