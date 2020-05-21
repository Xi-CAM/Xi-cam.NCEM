import itertools

from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem, FileDialog
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import CatalogView, FieldSelector, StreamSelector, ExportButton, BetterButtons


class NCEMViewerPlugin(StreamSelector, FieldSelector, ExportButton, BetterButtons, DynImageView, CatalogView, QWidget):
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

        dlg = FileDialog()
        outName = dlg.getSaveFileName(filter='tif')
        msg.logMessage(outName)

        md = self.header.descriptordocs[0]
        scale0 = (1.0 / float(md['PhysicalSizeX']), 1.0 / float(md['PhysicalSizeY']))
        msg.logMessage('meta data = {}'.format(type(scale0[0])))

        image = self.header.meta_array('primary')
        msg.logMessage('image type = {}'.format(type(image)))
        imsave('.'.join(outName),image,imagej=True,resolution=scale0, metadata={'unit': 'nm'})
