from pathlib import Path

from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
# from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

from xicam.core import msg
#from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import CatalogView

from .ncemimageview import NCEMImageView


class NCEMViewerPlugin(NCEMImageView, CatalogView, QWidgetPlugin):
    def __init__(self, catalog, stream: str = 'primary', field: str = 'raw',
                 toolbar: QToolBar = None, *args, **kwargs):

        self.header = None
        self.field = None

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
        # self.ui.gridLayout.addWidget(self.ui.menuBtn, 1, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.ui.graphicsView, 0, 0, 3, 1)

        # Setup coordinates label
        # self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        # self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)

        if catalog:
            self.setCatalog(catalog, stream=stream, field=field)

    # def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
    #     self.header = header
    #     self.field = field
    #     # make lazy array from document
    #     data = None
    #     try:
    #         data = header.meta_array(field)
    #     except IndexError:
    #         msg.logMessage(f'Header object contained no frames with field {field}.', msg.ERROR)
    #
    #     if data:
    #         if data.ndim > 1:
    #             # NOTE PAE: for setImage:
    #             #   use setImage(xVals=timeVals) to set the values on the slider for 3D data
    #             try:
    #                 # Retrieve the metadata for pixel scale and units
    #                 md = header.descriptordocs[0]
    #                 scale0 = (md['PhysicalSizeX'], md['PhysicalSizeY'])
    #                 units0 = (md['PhysicalSizeXUnit'], md['PhysicalSizeYUnit'])
    #             except:
    #                 scale0 = (1, 1)
    #                 units0 = ('', '')
    #                 msg.logMessage('NCEMviewer: No pixel size or units detected')
    #
    #             super(NCEMViewerPlugin, self).setImage(img=data, scale=scale0, *args, **kwargs)
    #
    #             self.axesItem.setLabel('bottom', text='X', units=units0[0])
    #             self.axesItem.setLabel('left', text='Y', units=units0[1])

    def export(self):
        from tifffile import imsave
        from pyqtgraph import FileDialog

        start_doc = getattr(self.catalog, self.stream).metadata['start']
        if 'FileName' in start_doc:
            current_dir = Path(start_doc['FileName']).parent
        else:
            current_dir = Path.home()

        # Get a file path to save to in current directory
        fd = FileDialog()
        fd.setNameFilter("TIF (*.tif)")
        fd.setDirectory(str(current_dir))
        fd.setFileMode(FileDialog.AnyFile)
        fd.setAcceptMode(FileDialog.AcceptSave)

        if fd.exec_():
            file_names = fd.selectedFiles()[0]
        outPath = Path(file_names)

        if outPath.suffix != '.tif':
            outPath = outPath.with_suffix('.tif')

        if 'PhysicalSizeX' in start_doc:
            #  Retrieve the metadata for pixel scale and units
            units0 = (start_doc['PhysicalSizeXUnit'], start_doc['PhysicalSizeYUnit'])
            scale0 = (start_doc['PhysicalSizeX'], start_doc['PhysicalSizeY'])

            # Change to nanometers if meters (for SER files)
            if units0[0] == 'm':
                units0 = ('nm', 'nm')
                scale0 = [ii*1e9 for ii in scale0]

        else:
            scale0 = (1, 1)
            units0 = ('', '')
            msg.logMessage('NCEMviewer: No pixel size or units detected')

        # Change scale from 1/pixel to pixel
        scale0 = [1/ii for ii in scale0]

        # Add units to metadata for imagej type output
        metadata = {'unit': units0[0]}

        # Get the data and change to float
        image = self.xarray[self.currentIndex, :, :].astype('f')

        imsave(outPath, image, imagej=True, resolution=scale0, metadata=metadata)
