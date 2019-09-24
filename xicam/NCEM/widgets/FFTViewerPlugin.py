import itertools

from xicam.plugins import QWidgetPlugin
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
import numpy as np
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from .NCEMViewerPlugin import NCEMViewerPlugin
import pyqtgraph as pg

class DynImageView_patch(DynImageView):
    ''' Patch to connect keyboard presses in timeline
    to emit a signal. This will be added as a patch to
    xicam in general.
    '''
    def evalKeyState(self):
        super(DynImageView_patch, self).evalKeyState()
        (ind, time) = self.timeIndex(self.timeLine)
        self.sigTimeChanged.emit(ind, time)

class FFTViewerPlugin(QWidgetPlugin):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        super(FFTViewerPlugin, self).__init__(*args, **kwargs)

        # Two Dynamic image views (maybe only need 1 for the main data. The FFT can be an ImageView()
        self.Rimageview = NCEMViewerPlugin()
        self.Fimageview = DynImageView_patch()
        # Keep Y-axis as is
        self.Rimageview.view.invertY(True)
        self.Fimageview.view.invertY(True)
        #self.Rimageview.imageItem.setOpts(axisOrder='col-major')
        #self.Fimageview.imageItem.setOpts(axisOrder='col-major')

        # Add to a layout
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.Rimageview)
        self.layout().addWidget(self.Fimageview)

        # Add ROI to real image
        # Retrieve the metadata for pixel scale and units
        
        #shape = (50, 50) # in pixels
        #self.Rroi = pg.RectROI(pos=(0, 0), size = (scale0[0] * shape[0], scale0[1] * shape[1]))
        self.Rroi = pg.RectROI(pos=(0, 0), size = (1,1))
        Rview = self.Rimageview.view.vb  # type: pg.ViewBox
        Rview.addItem(self.Rroi)
        
        # Hide the menu and roi buttons in the FFT view
        self.Fimageview.ui.menuBtn.setParent(None)
        self.Fimageview.ui.roiBtn.setParent(None)
        
        # Wireup signals
        self.Rroi.sigRegionChanged.connect(self.updateFFT)
        self.Rimageview.sigTimeChanged.connect(
            self.updateFFT)  # TODO: If you'd like, use sigTimeChangeFinished here instead?

        # Init vars
        self.header = None
        self.autoLevels = True
        # Set header
        if header: self.setHeader(header, field)
        
        #Initialize real space ROI size
        try:
            md = self.header.descriptordocs[0]
            scale0 = (md['PhysicalSizeX'], md['PhysicalSizeY'])
            units0 = (md['PhysicalSizeXUnit'], md['PhysicalSizeYUnit'])
        except:
            scale0 = (1, 1)
            units0 = ('','')
            msg.logMessage('FFTviewPlugin: No pixel size or units detected.')
        msg.logMessage('FFTviewPlugin: pixel size = {}'.format(scale0))
        self.Rroi.setPos((0,0))
        self.Rroi.setSize((scale0[0] * 50, scale0[1] * 50))
        self.Rimageview.autoRange()
        
    def updateFFT(self):
        '''Update the FFT diffractogram based on the Real space
        ROI location and size

        '''
        # get the frame data back from Rimageview (applies timeline slicing)
        try:
            data = self.Rimageview.imageItem.image
            
            # Get the pixel size
            try:
                md = self.header.descriptordocs[0]
                scale0 = (md['PhysicalSizeX'], md['PhysicalSizeY'])
                units0 = (md['PhysicalSizeXUnit'], md['PhysicalSizeYUnit'])
            except:
                scale0 = (1, 1)
                units0 = ('', '')
                msg.logMessage('FFTviewPlugin: No pixel size or units detected.')
            
            # Extract the data in the ROI
            x,y = self.Rroi.pos()
            w,h = self.Rroi.size()
            dataSlice = data[int(y/scale0[1]):int((y+h)/scale0[1]),int(x/scale0[0]):int((x+w)/scale0[0])]
            
            fft = np.fft.fft2(dataSlice)
            self.Fimageview.setImage(np.log(np.abs(np.fft.fftshift(fft)) + 1), autoLevels = self.autoLevels)
            self.autoLevels = False
            self.Rroi.setPen(pg.mkPen('w'))
        except ValueError:
            self.Rroi.setPen(pg.mkPen('r'))

    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.Rimageview.setHeader(header, field, *args, **kwargs)
        self.updateFFT()
        
