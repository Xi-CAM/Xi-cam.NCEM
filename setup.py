"""
Usage: pip install -e .
       python setup.py install
       python setup.py bdist_wheel
       python setup.py sdist bdist_egg
       twine upload dist/*
"""

from setuptools import setup, find_namespace_packages

setup(
    name='xicam.NCEM',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.5',

    description='A Xi-CAM plugin for viewing NCEM data.',

    # The project's main homepage.
    url='https://github.com/Xi-CAM/Xi-CAM.NCEM',

    # Author details
    author='Peter Ercius',
    author_email='percius@lbl.gov',

    # Choose your license
    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],

    # What does your project relate to?
    keywords='Electron Microscopy data viewing and analysis',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_namespace_packages(exclude=["docs", "tests*"]),

    package_dir={},

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["__init__"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    # xicam 2.3.0 and databroker 1.2.4 work
    install_requires=['ncempy>=1.7.0', 'tifffile', 'dask', 'numpy', 'databroker', 'qtpy', 'pyqtgraph',
                      'xicam==2.3.0','databroker<2'],

    setup_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,tests]
    extras_require={
        # 'dev': ['check-manifest'],
        'tests': ['pytest', 'coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[#('lib/python2.7/site-packages/gui', glob.glob('gui/*')),
    #            ('lib/python2.7/site-packages/yaml/tomography',glob.glob('yaml/tomography/*'))],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={"databroker.ingestors": ["application/x-DM = xicam.NCEM.ingestors.DMPlugin:ingest_NCEM_DM",
                                           "application/x-EMD = xicam.NCEM.ingestors.EMDPlugin:ingest_NCEM_EMD",
                                           "application/x-EMD-VELOX = xicam.NCEM.ingestors.EMDPlugin:ingest_NCEM_EMD_VELOX",
                                           "application/x-MRC = xicam.NCEM.ingestors.MRCPlugin:ingest_NCEM_MRC",
                                           "application/x-SER = xicam.NCEM.ingestors.SERPlugin:ingest_NCEM_SER",
                                           "image/tiff = xicam.NCEM.ingestors.TIFPlugin:ingest_NCEM_TIF"],
                  "databroker.sniffers": ['emd_sniffer = xicam.NCEM.ingestors.EMDPlugin:emd_sniffer', ],
                  "databroker.handlers": [],
                  "xicam.plugins.GUIPlugin": ["NCEM = xicam.NCEM:NCEMPlugin"],
                  "xicam.plugins.WidgetPlugin": ["ncem_viewer = xicam.NCEM.widgets.NCEMViewerPlugin:NCEMViewerPlugin"]
                  },

    ext_modules=[],
    include_package_data=True
)
