from pathlib import Path

from pyqtgraph import PlotItem
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import CatalogView, FieldSelector, StreamSelector, ExportButton, BetterButtons
from .ncemimageview import NCEMImageView


class NCEMViewerPlugin(StreamSelector, FieldSelector, ExportButton, BetterButtons,
                       CatalogView, QWidget):

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
        #self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        #self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)

        if catalog:
            self.setCatalog(catalog, stream=stream, field=field)

        start_doc = getattr(self.catalog, self.stream).metadata['start']

        if 'PhysicalSizeX' in start_doc:
            #  Retrieve the metadata for pixel scale and units
            scale0 = (start_doc['PhysicalSizeX'], start_doc['PhysicalSizeY'])
            units0 = (start_doc['PhysicalSizeXUnit'], start_doc['PhysicalSizeYUnit'])
        else:
            scale0 = (1, 1)
            units0 = ('', '')
            msg.logMessage('NCEMviewer: No pixel size or units detected')

        # Only way to set scale on the ImageView is to set the image again
        self.setImage(self.xarray, scale=scale0)

        self.axesItem.setLabel('bottom', text='X', units=units0[0])
        self.axesItem.setLabel('left', text='Y', units=units0[1])

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

        # Change scale from pixel to 1/pixel
        scale0 = [1/ii for ii in scale0]

        # Add units to metadata for Imagej type output
        metadata = {'unit': units0[0]}

        # Get the data and change to float
        image = self.xarray[self.currentIndex, :, :].astype('f')

        imsave(outPath, image, imagej=True, resolution=scale0, metadata=metadata)
