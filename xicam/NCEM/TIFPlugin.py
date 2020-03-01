from xicam.plugins.datahandlerplugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import functools
import tifffile


class TIFPlugin(DataHandlerPlugin):
    """ Loads single page (2D) and multi-page (3D) Tif files

    """

    name = 'TIFPlugin'

    DEFAULT_EXTENTIONS = ['.tif','tiff']

    descriptor_keys = ['object_keys']

    def __call__(self, index_z, index_t):
        data = tifffile.imread(self.path)
        
        if data.ndim == 3:
            im1 = data[index_t,:,:]
        elif data.ndim == 2:
            im1 = data
        
        return im1

    def __init__(self, path):
        super(TIFPlugin, self).__init__()
        self._metadata = None
        self.path = path
        #self.ser = tifffile.(self.path)

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:

            # Grab the metadata by temporarily instantiating the class and retrieving the metadata.
            # cls().metadata is not part of spec, but implemented here as a special case
            metadata = cls.parseDataFile(path)

            num_z = 1
            num_t = cls.num_t(path)

            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid,
                                                   'primary',
                                                   cls,
                                                   (path,),
                                                   {'index_z': index_z, 'index_t': index_t})

    @staticmethod
    def num_z(path):
        """ Only 3D Tiff files
        """
        return 1

    @staticmethod
    def num_t(path):
        """ Number of Tif pages
        """
        data = tifffile.TiffFile(path)
        num_t = len(data.pages)
        
        return num_t

    @classmethod
    def parseDataFile(cls, path):
        metaData = {}
        
        # Store the X and Y pixel size, offset and unit
        metaData['PhysicalSizeX'] = 1
        metaData['PhysicalSizeXOrigin'] = 0
        metaData['PhysicalSizeXUnit'] = ''
        metaData['PhysicalSizeY'] = 1
        metaData['PhysicalSizeYOrigin'] = 0
        metaData['PhysicalSizeYUnit'] = ''
        
        return metaData

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})

    @classmethod
    def getDescriptorDocs(cls, paths, start_uid, descriptor_uid):
        metadata = cls.parseTXTFile(paths[0])
        metadata.update(cls.parseDataFile(paths[0]))
        metadata.update({'object_keys': {'Unknown Device': ['Unknown Device']}})  # TODO: add device detection

        # TODO: Check with Peter if all keys should go in the descriptor, or if some should go in the events
        # metadata = dict([(key, metadata.get(key, None)) for key in getattr(self, 'descriptor_keys', [])])
        yield descriptor_doc(start_uid, descriptor_uid, metadata=metadata)
