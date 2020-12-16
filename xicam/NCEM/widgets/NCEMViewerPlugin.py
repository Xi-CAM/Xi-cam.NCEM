from pathlib import Path
import numpy as np

from pyqtgraph import InfLineLabel
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.gui.widgets.imageviewmixins import CatalogView, FieldSelector, StreamSelector, ExportButton, BetterButtons
from .ncemimageview import NCEMCatalogView


class NCEMViewerPlugin(StreamSelector, FieldSelector, ExportButton, BetterButtons,
                       NCEMCatalogView, QWidget):

    def __init__(self, catalog, stream: str = 'primary', field: str = 'raw',
                 toolbar: QToolBar = None, *args, **kwargs):

        self.header = None
        self.field = None

        # Add axes
        #self.axesItem = PlotItem()
        #self.axesItem.axes['left']['item'].setZValue(10)
        #self.axesItem.axes['top']['item'].setZValue(10)
        #if 'view' not in kwargs:
        #    kwargs['view'] = self.axesItem

        super(NCEMViewerPlugin, self).__init__(**kwargs)

        if catalog:
            self.setCatalog(catalog, stream=stream, field=field)

        # Use Viridis by default
        self.setPredefinedGradient("viridis")
        #self.imageItem.setOpts(axisOrder="col-major")
        #self.axesItem.invertY(False)

        self.imageItem.setOpts(axisOrder="row-major")

        # Set the physical scale on the xarray
        scale0, units0 = self._get_physical_size()

        self.xarray.coords['dim_1'] = scale0[0] * np.linspace(0, self.xarray.shape[-2] - 1, self.xarray.shape[-2])
        self.xarray.coords['dim_2'] = scale0[0] * np.linspace(0, self.xarray.shape[-1] - 1, self.xarray.shape[-1])

        self.xarray.attrs['units'] = units0[0]

        self.xarray = self.xarray.rename({'dim_1': ''.join(('Y ', units0[0])), 'dim_2': ''.join(('X ', units0[1]))})

        # Set the xarray to get the scale correct
        self.setImage(self.xarray)

        # Set a label on the infinite line if there are more than 20 images
        if self.xarray.shape[0] > 20:
            tlabel = InfLineLabel(self.timeLine, text="{value:.0f}")

        #self.axesItem.setLabel('bottom', text='X', units=units0[0])
        #self.axesItem.setLabel('left', text='Y', units=units0[1])

    def _get_physical_size(self):
        start_doc = getattr(self.catalog, self.stream).metadata['start']
        config = getattr(self.catalog, self.stream).metadata['descriptors'][0]['configuration']
        try:
            if 'PhysicalSizeX' in config:
                #  Retrieve the metadata for pixel scale and units
                scale0 = (config['PhysicalSizeX']['data']['PhysicalSizeX'],
                          config['PhysicalSizeY']['data']['PhysicalSizeY'])
                units0 = (config['PhysicalSizeXUnit']['data']['PhysicalSizeXUnit'],
                          config['PhysicalSizeYUnit']['data']['PhysicalSizeYUnit'])
            elif 'PhysicalSizeX' in start_doc:
                scale0 = (start_doc['PhysicalSizeX'],
                          start_doc['PhysicalSizeY'])
                units0 = (start_doc['PhysicalSizeXUnit'],
                          start_doc['PhysicalSizeYUnit'])
        except:
            scale0 = (1, 1)
            units0 = ('', '')
            msg.logMessage('NCEMviewer: No pixel size or units detected')

        return scale0, units0

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
        else:
            return

        if outPath.suffix != '.tif':
            outPath = outPath.with_suffix('.tif')

        scale0, units0 = self._get_physical_size()

        # Avoid overflow in field of view later
        if units0[0] == 'm':
            units0 = ['um', 'um']
            scale0 = [ii * 1e6 for ii in scale0]

        # Change scale from pixel to 1/pixel
        FOV = [1/ii for ii in scale0]

        # Add units to metadata for Imagej type output
        metadata = {'unit': units0[0]}

        # Get the data and change to float
        image = self.xarray[self.currentIndex, :, :].astype('f')

        imsave(outPath, image, imagej=True, resolution=FOV, metadata=metadata)
