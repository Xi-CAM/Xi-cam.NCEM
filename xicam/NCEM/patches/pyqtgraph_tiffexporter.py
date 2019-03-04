from pyqtgraph.parametertree import Parameter
from pyqtgraph.exporters import Exporter
import numpy as np
#from fabio import tifimage
from tifffile import imsave

from xicam.core import msg

class TIFFExporter(Exporter):
    Name = "Tiff Exporter"

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
        
        #GraphicsSceve, PlotItem, ImageItem
        #Get the ImageItem
        aa = self.item.getViewBox().allChildren()
        for ii in aa:
            msg.logMessage(f'children = {ii}')
        imItem = aa[1]
        msg.logMessage(f' image {imItem.image}')
        msg.logMessage(f' scale {imItem.scale()}') #this is a method. Not the actual pixel size. It just returns 1.0
        #Get the axes for the scale units
        bb = self.item.getAxis('bottom')
        msg.logMessage(f'export = {bb.labelUnits}')
        for item in self.item.addedItems:
            
            # You could set a flag on non-data imageitems within the same viewbox to filter them out
            # TODO: mark non-data imageitems as not-exportable
            if getattr(item, 'exportable', True):  # only the first exportable item will be exported
                image = item.image
                msg.logMessage('pixel size = {}'.format(item.pixelSize()))
                if self.params['Data Type']:
                    image = image.astype(self.params['Data Type'])
                #TODO: item.pixelSize() is not right. I need to find the scale and units of the axis. See above
                imsave(fileName,image,imagej=True,resolution=(item.pixelSize()[0],item.pixelSize()[1]),metadata={'unit':'nm'})
                break

    def parameters(self):
        return self.params
    

TIFFExporter.register()