from xicam.plugins.datahandlerplugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import functools
from ncempy.io import ser


class SERPlugin(DataHandlerPlugin):
    """ SER files that contain spectra are currently not supported.

    """

    name = 'SERPlugin'

    DEFAULT_EXTENTIONS = ['.ser']

    descriptor_keys = ['object_keys']

    def __call__(self, index_z, index_t):
        im1 = self.ser.getDataset(index_t)[0]
        return im1

    def __init__(self, path):
        super(SERPlugin, self).__init__()
        self._metadata = None
        self.path = path
        self.ser = ser.fileSER(self.path)

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:

            # Grab the metadata by temporarily instantiating the class and retrieving the metadata.
            # cls().metadata is not part of spec, but implemented here as a special case
            metadata = cls.metadata(path)

            num_z = 1
            num_t = metadata['ValidNumberElements']

            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid,
                                                   'primary',
                                                   cls,
                                                   (path,),
                                                   {'index_z': index_z, 'index_t': index_t})

    # num_z and num_t are trivial, but they're preserved here to mirror other NCEM file interfaces

    @staticmethod
    def num_z(metadata):
        """ Ser files can only by 3D in nature
        """
        return 1

    @staticmethod
    def num_t(metadata):
        """ The number of data sets in the ser file. SER files are always laid out as a 'series'
        of 1D or 2D datasets. Thus, you need to retrieve each data set in the series separately.

        2D data sets:
        For series of 2D datasets this is a layout of X,Y for each data set

        1D data sets (unuspported!)
        For series of 1D data sets (spectra) this is a layout of 1 spectra at each position
        in a 1D or 2D raster.

        Note: Each data set can have a different X-Y size. Its rare but possible.
        """

        if metadata['DataTypeID'] == 16674:
            # 2D data sets (images)
            return metadata['ValidNumberElements']
        elif metadata['DataTypeID'] == 16672:
            # 1D data sets (currently unsupported)
            return metadata['ValidNumberElements']

        return None

    @classmethod
    def parseDataFile(cls, path):
        metaData = cls.metadata(path)

        # Store the X and Y pixel size, offset and unit
        metaData['PhysicalSizeX'] = metaData['Calibration'][0]['CalibrationDelta']
        metaData['PhysicalSizeXOrigin'] = metaData['Calibration'][0]['CalibrationOffset']
        metaData['PhysicalSizeXUnit'] = 'm' #always meters
        metaData['PhysicalSizeY'] = metaData['Calibration'][1]['CalibrationDelta']
        metaData['PhysicalSizeYOrigin'] = metaData['Calibration'][1]['CalibrationOffset']
        metaData['PhysicalSizeYUnit'] = 'm' #always meters
        
        metaData['FileName'] = path
        
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

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def metadata(path):
        with ser.fileSER(path,emifile=False) as ser1:
            data, metaData = ser1.getDataset(0)  # have to get 1 image and its meta data
            
            # Get extra meta data from the EMI file if it exists
            emifile = path[:-6] + '.emi'
            if os.path.exists(emifile):
                _emi = ser1.read_emi(emifile)
                metaData.update(_emi)
        
        metaData.update(ser1.head)  # some header data for the ser file
        
        # Clean the dictionary
        for k, v in metaData.items():
            if isinstance(v, bytes):
                metaData[k] = v.decode('UTF8')
        return metaData
