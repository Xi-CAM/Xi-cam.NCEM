from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtCore import QRect, QRectF

import numpy as np
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
#import pyqtgraph as pg

# TODO: single-source with SAXSViewerPlugin


class FFTViewerPlugin(QWidgetPlugin, QWidgetPlugin):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        
        #Two Dynamic image views
        self.Rimageview = DynImageView()
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
        self.Rroi = pg.RectROI(pos=(0, 0), size=(10, 10), translateSnap=True, snapSize=1, scaleSnap=True)
        self.Rroi.sigRegionChanged.connect(self.updateFFT)
        Rview = self.Rimageview.view  # type: pg.ViewBox
        Rview.addItem(self.Rroi)
        
        super(FFTViewerPlugin, self).__init__(**kwargs)
        
        # Setup axes reset button 
        self.resetAxesBtn = QPushButton('Reset Axes')
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetAxesBtn.sizePolicy().hasHeightForWidth())
        self.resetAxesBtn.setSizePolicy(sizePolicy)
        self.resetAxesBtn.setObjectName("resetAxes")
        self.ui.gridLayout.addWidget(self.resetAxesBtn, 2, 1, 1, 1)
        self.resetAxesBtn.clicked.connect(self.autoRange)

        # Setup LUT reset button
        self.resetLUTBtn = QPushButton('Reset LUT')
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetLUTBtn.sizePolicy().hasHeightForWidth())
        # self.resetLUTBtn.setSizePolicy(sizePolicy)
        # self.resetLUTBtn.setObjectName("resetLUTBtn")
        self.ui.gridLayout.addWidget(self.resetLUTBtn, 3, 1, 1, 1)
        self.resetLUTBtn.clicked.connect(self.autoLevels)

        # Hide ROI button and rearrange
        self.ui.roiBtn.setParent(None)
        self.ui.gridLayout.addWidget(self.ui.menuBtn, 1, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.ui.graphicsView, 0, 0, 3, 1)

        # Setup coordinates label
        self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)

        # Set header
        if header: self.setHeader(header, field)
    
    def updateFFT(self, data):
        '''Update the FFT diffractogram based on the Real space
        ROI location and size
        
        '''
        fft = np.abs(np.fft.fft2(self.data))
        self.Fimageview.setImage(np.log(data[int(self.Rroi.pos().x()):int(self.Rroi.pos().x() + self.Rroi.size().x()),int(self.Rroi.pos().y()):int(self.Rroi.pos().y() + self.Rroi.size().y())] + 1))
    
    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.field = field
        # make lazy array from document
        data = None
        try:
            data = header.meta_array(field)
        except IndexError:
            msg.logMessage('Header object contained no frames with field {field}.', msg.ERROR)

        if data:
            # data = np.squeeze(data) #test for 1D spectra
            if data.ndim > 1:
                # kwargs['transform'] = QTransform(0, -1, 1, 0, 0, data.shape[-2])
                #NOTE PAE: for setImage:
                #   use setImage(xVals=timeVals) to set the values on the slider for 3D data
                try:
                    #Unified meta data for pixel scale and units
                    scale0 = (header.descriptors[0]['PhysicalSizeX'],header.descriptors[0]['PhysicalSizeY'])
                    units0 = (header.descriptors[0]['PhysicalSizeXUnit'],header.descriptors[0]['PhysicalSizeYUnit'])
                except:
                    scale0 = [1, 1]
                    units0 = ['', '']
                    #msg.logMessage{'NCEMviewer: No pixel size or units detected'}
                super(NCEMViewerPlugin, self).setImage(img=data, scale=scale0, *args, **kwargs)
                self.axesItem.setLabel('bottom', text='X', units=units0[0])
                self.axesItem.setLabel('left', text='Y', units=units0[1])
            #else:
            #    msg.logMessage('Cant load 1D data.')
