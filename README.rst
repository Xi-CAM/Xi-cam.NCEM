========
Xi-cam.NCEM
========

A plugin for the LBNL CAMERA Xi-cam1 image program for electron microscopy data analysis supported by the National Center for Electron Microscopy facility of the Molecular Foundry.

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

**Viewer**
    Opens and displays 1D, 2D and 3D versions of hte files mentioned above.

**FFTViewer**
    Shows the real space and 'live' FFT diffractogram of a chosen region of the image.

Installation
============

Installation is only supported using source code available at the Camera Github Repositories

Here are a set of steps to install this program using git, conda, and pip on Windows:
.. code-block:: bash
   :emphasize-lines: 3,5

    git clone git@github.com:lbl-camera/Xi-cam.gui.git
    git clone git@github.com:lbl-camera/Xi-cam.plugins.git
    git clone git@github.com:lbl-camera/Xi-cam.core.git
    git clone git@github.com:lbl-camera/Xi-cam.git

    git clone git@github.com:ercius/Xi-cam.NCEM.git

Create a new conda environment. Some dependencies are installed by pip.
.. code-block:: bash
    conda create --name xicam2 python=3.7 numpy scipy dask jupyter h5py pyqtgraph matplotlib
    activate xicam2
    pip install -e Xi-cam.core\
    pip install -e Xi-cam.plugins\
    pip install -e Xi-cam.gui\
    pip install -e Xi-cam.NCEM\
    pip install -e Xi-cam\