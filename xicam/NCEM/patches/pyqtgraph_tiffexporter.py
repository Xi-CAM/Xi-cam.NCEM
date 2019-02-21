from pyqtgraph.parametertree import Parameter
from pyqtgraph.exporters import Exporter
import numpy as np


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

        for item in self.item.addedItems:
            # You could set a flag on non-data imageitems within the same viewbox to filter them out
            # TODO: mark non-data imageitems as not-exportable
            if getattr(item, 'exportable', True):  # only the first exportable item will be exported
                image = item.image
                if self.params['Data Type']:
                    image = image.astype(self.params['Data Type'])
                tif = tifimage.TifImage(image)
                tif.header.update({'key': 'value'})  # put metadata here
                tif.write(fileName)
                break

    def parameters(self):
        return self.params
    

TIFFExporter.register()