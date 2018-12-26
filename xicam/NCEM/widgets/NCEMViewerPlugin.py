from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import numpy as np
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
import pyqtgraph as pg

# TODO: single-source with SAXSViewerPlugin


class NCEMViewerPlugin(DynImageView, QWidgetPlugin):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):

        # Add axes
        self.axesItem = PlotItem()
        # self.axesItem.setLabel('bottom', u'q ()')  # , units='s')
        # self.axesItem.setLabel('left', u'q ()')
        self.axesItem.axes['left']['item'].setZValue(10)
        self.axesItem.axes['top']['item'].setZValue(10)
        if 'view' not in kwargs: kwargs['view'] = self.axesItem

        super(NCEMViewerPlugin, self).__init__(**kwargs)
        self.axesItem.invertY(False)

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

    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.field = field
        # make lazy array from document
        data = None
        try:
            data = header.meta_array(field)
        except IndexError:
            msg.logMessage('Header object contained no frames with field ''{field}''.', msg.ERROR)

        if data:
            # data = np.squeeze(data) #test for 1D spectra
            if data.ndim > 1:
                # kwargs['transform'] = QTransform(0, -1, 1, 0, 0, data.shape[-2])
                #NOTE PAE: for setImage:
                #   use scale = [xPixSize,yPixSize] to calibrate the pixelSize
                #   use pg.PlotItem.setLabel('bottom', text='x axis title', units='m') 
                #   use setImage(xVals=timeVals) to set the values on the slider for 3D data
                try:
                    # header.startdoc, header.stopdoc, header.desciptordocs[ii], header.eventdocs[jj]
                    ftype = header.descriptors[0]['file type']
                    if ftype == 'ser':
                        # SER file
                        scale0 = []
                        units0 = []
                        for cal in header.descriptors[0]['Calibration']:
                            scale0.append(cal['CalibrationDelta'])
                            units0.append('m')
                    else:
                        #Unified meta data for pixel scale and units
                        scale0 = (header.descriptors[0]['PhysicalSizeX'],header.descriptors[0]['PhysicalSizeY'])
                        units0 = (header.descriptors[0]['PhysicalSizeXUnit'],header.descriptors[0]['PhysicalSizeYUnit'])
                except:
                    scale0 = [1, 1]
                    units0 = ['', '']
                super(NCEMViewerPlugin, self).setImage(img=data, scale=scale0, *args, **kwargs)
                self.axesItem.setLabel('bottom', text='X', units=units0[0])
                self.axesItem.setLabel('left', text='Y', units=units0[1])
            #else:
            #    msg.logMessage('Cant load 1D data.')
