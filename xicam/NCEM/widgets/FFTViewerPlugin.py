from xicam.plugins import QWidgetPlugin
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
import numpy as np
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from .NCEMViewerPlugin import NCEMViewerPlugin
import pyqtgraph as pg


class FFTViewerPlugin(QWidgetPlugin):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        super(FFTViewerPlugin, self).__init__(*args, **kwargs)
        
        #Two Dynamic image views (maybe only need 1 for the main data. The FFT can be an ImageView()
        self.Rimageview = NCEMViewerPlugin()
        self.Fimageview = DynImageView()
        # Keep Y-axis as is
        self.Rimageview.view.invertY(True)
        self.Fimageview.view.invertY(True)
        self.Rimageview.imageItem.setOpts(axisOrder='col-major')
        self.Fimageview.imageItem.setOpts(axisOrder='col-major')

        #Add to a layout
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.Rimageview)
        self.layout().addWidget(self.Fimageview)
        
        #Add ROI to real image
        scale = header.descriptors[0]['PhysicalSizeX'], header.descriptors[0]['PhysicalSizeY']
        shape = header.descriptors[0]['ArrayShape']
        self.Rroi = pg.RectROI(pos=(0, 0), size=(scale[0] * shape[0], scale[1] * shape[1]))
        Rview = self.Rimageview.view.vb  # type: pg.ViewBox
        Rview.addItem(self.Rroi)

        # Wireup signals
        self.Rroi.sigRegionChanged.connect(self.updateFFT)
        self.Rimageview.sigTimeChanged.connect(
            self.updateFFT)  # TODO: If you'd like, use sigTimeChangeFinished here instead?

        # Set header
        if header: self.setHeader(header, field)

    def updateFFT(self):
        '''Update the FFT diffractogram based on the Real space
        ROI location and size

        '''
        # get the frame data back from Rimageview (applies timeline slicing)
        try:
            data = self.Rimageview.image[self.Rimageview.currentIndex]
            dataslice = self.Rroi.getArrayRegion(data, self.Rimageview.imageItem)

            fft = np.abs(np.fft.fft2(dataslice))
            self.Fimageview.setImage(np.log(np.abs(np.fft.fftshift(fft)) + 1))
            self.Rroi.setPen(pg.mkPen('w'))
        except ValueError:
            self.Rroi.setPen(pg.mkPen('r'))
    
    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.Rimageview.setHeader(header, field, *args, **kwargs)
        self.updateFFT()
