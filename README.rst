========
Xi-cam.NCEM
========

A plugin for the LBNL CAMERA Xi-cam image program for electron microscopy data analysis supported by the National Center for Electron Microscopy facility of the Molecular Foundry.

This plugin is the main grpahical user interface for the ncempy pypiu package for visualizing electron microscopy data.

Supported file types are:
 - Digital Micrograph version 3 and 4
 - Thermo Fischer (FEI) SER files
 - Thermo Fischer (FEI) EMD files written by Velox
 - Berkeley EMD files
 - MRC format files

Components
==========

The Xi-cam.NCEM plugin implements two types of image viewing

**View**
    Opens and displays 1D, 2D and 3D versions of hte files mentioned above.

**FFTView**
    Shows the real space image and 'live' FFT diffractogram of a chosen region of the image.

Installation
============

Here are a set of steps to install this program using git, conda, and pip on Windows. Installation is only supported using source code available at the Camera Github Repositories

Clone the following repositories from synchrotrons on github
    git clone git@github.com:synchrotrons/Xi-cam.gui.git
    
    git clone git@github.com:synchrotrons/Xi-cam.plugins.git
    
    git clone git@github.com:synchrotrons/Xi-cam.core.git

    git clone git@github.com:synchrotrons/Xi-cam.git

Either get the stable NCEM plugin from synchrotons
	git clone git@github.com:synchrotrons/Xi-cam.NCEM.git

OR the development version from Ercius
    git clone git@github.com:ercius/Xi-cam.NCEM.git

Create and activate a new conda environment. Some dependencies are installed by pip.
    conda create --name xicam2 python=3.7 numpy scipy dask jupyter h5py pyqtgraph matplotlib netcdf4 xarray requests astropy
    
    activate xicam2


Run the following pip commands from the parent directory of the cloned repositories above.
 - Note: Slashes (\\ on windows and / on Linux or Mac) at the end of the line are important to force a local installation rather than downloading from pypi
    pip install -e Xi-cam.core\\
    
    pip install -e Xi-cam.plugins\\
    
    pip install -e Xi-cam.gui\\
    
    pip install -e Xi-cam.NCEM\\
    
    pip install -e Xi-cam\\

Update all xicam packages.

    #!/bin/bash
    
    echo xi-cam

    cd ./xi-cam

    git pull

    echo xi-cam.plugins

    cd ../xi-cam.plugins

    git pull

    echo xi-cam.gui

    cd ../xi-cam.gui

    git pull

    echo xi-cam.core

    cd ../xi-cam.core

    git pull

    echo xicam.NCEM
    cd ../xi-cam.NCEM
    git pull

    cd ..

Debugging
=========
Xicam allows the user to just call the xicam executable to run which is very convenient. However, there is then no way to capture simple console output (other than msg.logMessage) or use pdb debugging. Debugging in QT is possible based on this StackOverflow answer.

Follow these steps (copied here for my and others convenience if needed):

Find the xicam-script.pyw file in your environment's /Scripts folder
for example ~/Anaconda3/envs/xicam2/Scripts
Copy this file to xicam-script.py (no w in the extension)
If you now execute python xicam-script.py the console output is shown in that console.
Incidentally, use pythonw xicam-script.py to stop printing to console
To enable debugging insert this code where you want to stop the program
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
Resuming might be possible using
from PyQt5.QtCore import pyqtRestoreInputHook
pyqtRestoreInputHook()
and then pressing CTRL-C to stop the command printing. I have not tried this though.

Logging
=======
Logging
The log directoy location was recently moved. Xicam now uses appdirs (from pypi) to determine the location of certainpaths. These are now set in:
Xi-cam.core\xicam\core\paths.py

On my windows machine the log is now located at:
C:\Users\<username>\AppData\Local\xicam\xicam\Cache\logs\out.log

To determine this location:
(xicam) > python
>> import appdirs
>> appdirs.user_cache_dir()