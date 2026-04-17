@echo off
REM Build MetaTag project
REM Prerequisites: CMake, Visual Studio 2022, vcpkg installed at C:\vcpkg

setlocal enabledelayedexpansion

REM Set CMake and vcpkg paths
set CMAKE_EXE="C:\Program Files\CMake\bin\cmake.exe"
set VCPKG_ROOT=C:\vcpkg
set VCPKG_EXE=%VCPKG_ROOT%\vcpkg.exe

echo [1/4] Installing dependencies via vcpkg (this may take 30-60 minutes on first run)...
%VCPKG_EXE% install qt:x64-windows taglib:x64-windows --vcpkg-root %VCPKG_ROOT%
if %ERRORLEVEL% neq 0 (
    echo Error: vcpkg install failed
    exit /b 1
)

echo.
echo [2/4] Cleaning previous build...
rmdir /s /q build 2>nul
mkdir build 2>nul

echo.
echo [3/4] Configuring CMake...
cd build
%CMAKE_EXE% .. ^
    -G "Visual Studio 17 2022" ^
    -DCMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%/scripts/buildsystems/vcpkg.cmake ^
    -DCMAKE_BUILD_TYPE=Release
if %ERRORLEVEL% neq 0 (
    echo Error: CMake configure failed
    exit /b 1
)

echo.
echo [4/4] Building project...
%CMAKE_EXE% --build . --config Release
if %ERRORLEVEL% neq 0 (
    echo Error: Build failed
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable: build\src\ui\Release\metatag-ui.exe
cd ..
pause
