from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import uuid
import re
import functools
from pathlib import Path
from ncempy.io import ser
from xicam.core import msg


# TODO: add __enter__ and 'with' support to this plugin

class SERPlugin(DataHandlerPlugin):
    '''SER files that contain spectra are currently not supported.
    
    '''

    name = 'SERPlugin'

    DEFAULT_EXTENTIONS = ['.ser']

    descriptor_keys = ['']

    def __call__(self, path, index_z, index_t):
        ser1 = ser.fileSER(path)
        im1 = ser1.getDataset(index_t)[0]
        del ser1
        return im1

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        msg.logMessage('SER getEventDocs called')
        for path in paths:
            num_z = cls.num_z(path)  # ser files can only be 3D (no 4D)
            num_t = cls.num_t(path)
            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path, index_z, index_t))

    @staticmethod
    def num_z(path):
        '''Ser files can only by 3D in nature
        '''
        return 1

    @staticmethod
    def num_t(path):
        '''The number of data sets in the ser file. SER files are always laid out as a 'series'
        of 1D or 2D datasets. Thus, you need to retrieve each data set in the series separately.
        
        2D data sets:
        For series of 2D datasets this is a layout of X,Y for each data set
        
        1D data sets (unuspported!)
        For series of 1D data sets (spectra) this is a layout of 1 spectra at each position
        in a 1D or 2D raster.
        
        Note: Each data set can have a different X-Y size. Its rare but possible.        
        '''

        ser1 = ser.fileSER(path)
        if ser1.head['DataTypeID'] == 16674:
            # 2D data sets (images)
            out = ser1.head['ValidNumberElements']
        elif ser1.head['DataTypeID'] == 16672:
            # 1D data sets (currently unsupported)
            out = ser1.head['ValidNumberElements']

        del ser1
        return out    
    
    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        ser1 = ser.fileSER(path)
        data, metaData = ser1.getDataset(0)
        del ser1
        metaData['file type'] = 'ser'

        return metaData

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})

    @classmethod
    def getDescriptorDocs(cls, paths, start_uid, descriptor_uid):
        metadata = cls.parseTXTFile(paths[0])
        metadata.update(cls.parseDataFile(paths[0]))

        # TODO: Check with Peter if all keys should go in the descriptor, or if some should go in the events
        # metadata = dict([(key, metadata.get(key, None)) for key in getattr(cls, 'descriptor_keys', [])])
        yield descriptor_doc(start_uid, descriptor_uid, metadata=metadata)
