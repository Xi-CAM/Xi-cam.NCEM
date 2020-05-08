===========
Xi-cam.NCEM
===========

A plugin for the Xi-cam image program for electron microscopy data visualization supported by the National Center for Electron Microscopy facility of the Molecular Foundry.

This plugin is the main graphical user interface for the
`openNCEM ncempy <https://openncem.readthedocs.io/en/latest/ncempy.html>`_
package for visualizing electron microscopy data.

Supported file types are:

- Digital Micrograph version 3 and 4
- Thermo Fischer (FEI) SER files
- Thermo Fischer (FEI) EMD files written by Velox
- Berkeley EMD files
- MRC format files
- TIF files with ImageJ metadata

Components
==========

The Xi-cam.NCEM plugin implements two types of data viewing

**View**
    Opens and displays 2D and 3D versions of the files mentioned above.

**FFTView**
    Shows the real space image and 'live' FFT diffractogram of a chosen region of the image.

Installation
============

Here are a set of steps to install this program using git, conda, and pip on
Windows. Installation is currently only supported using source code available at the
Github repositories. A release is coming soon.

1. Clone the unified repository from `XI-CAM <https://github.com/Xi-CAM>`_ on github

::

    git clone https://github.com/Xi-CAM/Xi-cam-unified.git
    
2a. Get the stable `Xi-cam.NCEM <https://github.com/Xi-CAM/Xi-cam.NCEM>`_ plugin from XI-CAM

::

    git clone https://github.com/Xi-CAM/Xi-cam.NCEM.git

2b. OR the development version from
`Peter Ercius's repository <https://github.com/ercius/Xi-cam.NCEM>`_

::

    git clone https://github.com/ercius/Xi-cam.NCEM.git

3. Create and activate a new conda environment. Some dependencies are installed by pip later.

::

    conda create --name xicam python=3.7 numpy scipy dask jupyter h5py pyqtgraph matplotlib netcdf4 xarray requests astropy numcodecs pyqt intake humanize
    activate xicam

4. Run the following pip commands from the parent directory of the cloned repositories above.

::

    pip install -e Xi-cam-unified\\
    pip install -e Xi-cam.NCEM\\

- Note: Slashes (\\ on windows and / on Linux or Mac) at the end of the line are important to force a local installation rather than downloading from pypi
- Note: The -e option installs the packages as 'editable' so you can update the program easily using git

Debugging
=========
Xicam allows the user to just call the xicam executable from anywhere
once the anaconda environment is activated, which is very convenient.
However, there the error is captured by a logger (see below)
and debugging is difficult.
Debugging in QT is possible using the steps below.

Follow these steps:

1. Find the xicam-script.pyw file in your environment's ../Scripts folder
for example ~/Anaconda3/envs/xicam2/Scripts

Execute this in the command prompt

::

    python xicam-script.py

The console output is shown in that console including error messages.

Alternatively, to stop printing to console use

::

    pythonw xicam-script.py

To enable debugging for a pyqt program insert this code where you want to stop the program

::

    from PyQt5.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()

Resuming might be possible using

::

    from PyQt5.QtCore import pyqtRestoreInputHook
    pyqtRestoreInputHook()

and then pressing CTRL-C to stop the command printing. I have not tried this though.

Logging
=======

The log directory location was recently moved. Xicam now uses appdirs (from pypi) to determine the location of certainpaths. These are now set in:
Xi-cam.core\xicam\core\paths.py

On my windows machine the log is now located at:

C:\\Users\\<username>\\AppData\\Local\\xicam\\xicam\\Cache\\logs\\out.log

To determine this location, start python and run the following code:

::

    import appdirs
    print(appdirs.user_cache_dir())
