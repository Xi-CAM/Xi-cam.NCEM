from xicam.plugins import QWidgetPlugin
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
import numpy as np
from xicam.core import msg
#from xicam.gui.widgets.dynimageview import DynImageView
#from xicam.gui.widgets.imageviewmixins import CatalogView, QCoordinates, QSpace
from .NCEMViewerPlugin import NCEMViewerPlugin
import pyqtgraph as pg

from .ncemimageview import NCEMImageView


class FFTViewerPlugin(QWidgetPlugin):
    def __init__(self, catalog, stream: str = 'primary', field: str = 'raw', toolbar: QToolBar = None, *args, **kwargs):

        self.stream = stream
        self.field = field
        self.catalog = catalog

        super(FFTViewerPlugin, self).__init__(*args, **kwargs)

        # Two NCEM image views
        self.Rimageview = NCEMViewerPlugin(catalog)
        #self.Fimageview = DynImageView_patch()
        self.Fimageview = NCEMImageView()
        # Keep Y-axis as is
        self.Rimageview.view.invertY(True)
        self.Fimageview.view.invertY(True)
        # self.Rimageview.imageItem.setOpts(axisOrder='col-major')
        # self.Fimageview.imageItem.setOpts(axisOrder='col-major')

        # Add to a layout
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.Rimageview)
        self.layout().addWidget(self.Fimageview)

        # Add ROI to real image
        # Retrieve the metadata for pixel scale and units
        self.Rroi = pg.RectROI(pos=(0, 0), size=(1, 1))
        self.Rimageview.view.vb.addItem(self.Rroi)

        # Hide the menu and roi buttons in the FFT view
        self.Fimageview.ui.menuBtn.setParent(None)
        self.Fimageview.ui.roiBtn.setParent(None)

        # Wireup signals
        self.Rroi.sigRegionChanged.connect(self.updateFFT)
        self.Rimageview.sigTimeChanged.connect(
            self.updateFFT)  # TODO: If you'd like, use sigTimeChangeFinished here instead?

        # Init vars
        # self.header = None
        self.autoLevels = True
        # Set catalog
        if catalog:
            self.setCatalog(catalog, stream=stream, field=field)

        # Initialize real space ROI size
        start_doc = getattr(self.Rimageview.catalog, stream).metadata['start']

        if 'PhysicalSizeX' in start_doc:
            #  Retrieve the metadata for pixel scale and units
            scale0 = (start_doc['PhysicalSizeX'], start_doc['PhysicalSizeY'])
            units0 = (start_doc['PhysicalSizeXUnit'], start_doc['PhysicalSizeYUnit'])
        else:
            scale0 = (1, 1)
            units0 = ('', '')
            msg.logMessage('FFTviewer: No pixel size or units detected')

        # Workaround to add the scale to the image
        self.Rimageview.setImage(self.Rimageview.xarray, scale=scale0)

        # Set the starting position of the real ROI
        sh = self.Rimageview.xarray.shape
        sz = [int(ii / 8) for ii in sh]
        self.Rroi.setPos((scale0[-1]*(sh[-1]/2-sz[-1]/2), scale0[-2]*(sh[-2]/2-sz[-2]/2)))
        self.Rroi.setSize((scale0[-1] * sz[-1], scale0[-2] * sz[-2]))
        self.Rimageview.autoRange()

    def updateFFT(self):
        """ Update the FFT diffractogram based on the Real space
        ROI location and size

        """
        # get the frame data back from Rimageview (applies timeline slicing)
        try:
            data = self.Rimageview.imageItem.image

            start_doc = getattr(self.Rimageview.catalog, self.stream).metadata['start']
            # Get the pixel size
            if 'PhysicalSizeX' in start_doc:
                scale0 = (start_doc['PhysicalSizeX'], start_doc['PhysicalSizeY'])
                units0 = (start_doc['PhysicalSizeXUnit'], start_doc['PhysicalSizeYUnit'])
            else:
                scale0 = (1, 1)
                units0 = ('', '')
                msg.logMessage('FFTviewPlugin: No pixel size or units detected.')

            # Extract the data in the ROI
            x, y = self.Rroi.pos()
            w, h = self.Rroi.size()
            dataSlice = data[int(y / scale0[1]):int((y + h) / scale0[1]), int(x / scale0[0]):int((x + w) / scale0[0])]

            fft = np.fft.fft2(dataSlice)
            self.Fimageview.setImage(np.log(np.abs(np.fft.fftshift(fft)) + 1))  # , autoLevels = self.autoLevels)
            self.autoLevels = False
            self.Rroi.setPen(pg.mkPen('w'))
        except ValueError:
            self.Rroi.setPen(pg.mkPen('r'))

    def setCatalog(self, catalog: NonDBHeader, stream: str, field: str, *args, **kwargs):
        self.Rimageview.setCatalog(catalog, stream, field, *args, **kwargs)
        self.updateFFT()
