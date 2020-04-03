from pyqtgraph.parametertree import Parameter
from pyqtgraph.exporters import Exporter
import numpy as np
#from fabio import tifimage
from tifffile import imsave

from xicam.core import msg

class TIFFExporter(Exporter):
    Name = "Tiff Data Exporter"

    def __init__(self, item):
        Exporter.__init__(self, item)

        # Exporter config options
        self.params = Parameter(name='params', type='group', children=[
            {'name': 'Data Type', 'type': 'list', 'value': 'int', 'values': {'Default [Preserve Raw Type]': None,
                                                                             'float': np.float,
                                                                             'int': np.int, }},

        ])

    def export(self, fileName=None, toBytes=False, copy=False):

        if fileName is None:
            self.fileSaveDialog(filter=["*.tif"])
            return

        # GraphicsScene, PlotItem, ImageItem
        # Get the ImageItem
        aa = self.item.getViewBox().allChildren()
        imItem = aa[1]
        # Get the axes for the scale units
        bottomAxis = self.item.getAxis('bottom')
        
        # debug
        from PyQt5.QtCore import pyqtRemoveInputHook
        from pdb import set_trace
        pyqtRemoveInputHook()
        set_trace()
        
        for item in self.item.addedItems:

            # You could set a flag on non-data imageitems within the same viewbox to filter them out
            # TODO: mark non-data imageitems as not-exportable
            if getattr(item, 'exportable', True):  # only the first exportable item will be exported
                image = item.image
                if self.params['Data Type']:
                    image = image.astype(self.params['Data Type'])
                #TODO: item.pixelSize() is not right. I need to find the scale and units of the axis. See above
                imsave(fileName,image.astype(),imagej=True,resolution=(imItem.scaleNCEM[0], imItem.scaleNCEM[1]), metadata={'unit':'nm'})
                break

    def parameters(self):
        return self.params
    

TIFFExporter.register()