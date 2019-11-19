import itertools

from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem, FileDialog
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView

class NCEMViewerPlugin(DynImageView, QWidgetPlugin):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):

        # Add axes
        self.axesItem = PlotItem()
        self.axesItem.axes['left']['item'].setZValue(10)
        self.axesItem.axes['top']['item'].setZValue(10)
        if 'view' not in kwargs: kwargs['view'] = self.axesItem

        super(NCEMViewerPlugin, self).__init__(**kwargs)
        self.axesItem.invertY(True)

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
        
        # Export button
        self.exportBtn = QPushButton('Export')
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.exportBtn.sizePolicy().hasHeightForWidth())
        self.ui.gridLayout.addWidget(self.exportBtn, 4, 1, 1, 1)
        self.exportBtn.clicked.connect(self.export)
        
        # Hide ROI button and the Menu button and rearrange
        self.ui.roiBtn.setParent(None)
        self.ui.menuBtn.setParent(None)
        #self.ui.gridLayout.addWidget(self.ui.menuBtn, 1, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.ui.graphicsView, 0, 0, 3, 1)

        # Setup coordinates label
        #self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        #self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)
        
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
            msg.logMessage(f'Header object contained no frames with field {field}.', msg.ERROR)
        
        if data:
            if data.ndim > 1:
                #NOTE PAE: for setImage:
                #   use setImage(xVals=timeVals) to set the values on the slider for 3D data
                try:
                    # Retrieve the metadata for pixel scale and units
                    md = header.descriptordocs[0]
                    scale0 = (md['PhysicalSizeX'], md['PhysicalSizeY'])
                    units0 = (md['PhysicalSizeXUnit'], md['PhysicalSizeYUnit'])
                except:
                    scale0 = (1, 1)
                    units0 = ('', '')
                    msg.logMessage('NCEMviewer: No pixel size or units detected')
                    
                super(NCEMViewerPlugin, self).setImage(img=data, scale=scale0, *args, **kwargs)
                
                self.axesItem.setLabel('bottom', text='X', units=units0[0])
                self.axesItem.setLabel('left', text='Y', units=units0[1])
    
    def export(self):
        from tifffile import imsave

        #outName = self.fileSaveDialog(filter=["*.tif"])
        dlg = FileDialog()
        outName = dlg.getSaveFileName(filter='tif')
        msg.logMessage(outName)
        
        md = self.header.descriptordocs[0]
        scale0 = (md['PhysicalSizeX'], md['PhysicalSizeY'])
        msg.logMessage('meta data = {}'.format(scale0[0]))
        
        image = self.header.meta_array('primary')
        msg.logMessage('image type = {}'.format(type(image)))
        imsave('.'.join(outName),image,imagej=True,resolution=scale0, metadata={'unit':'nm'})
        