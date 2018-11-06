from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path
from xicam.core import msg
from ncempy.io import mrc

class MRCPlugin(DataHandlerPlugin):
    name = 'MRCPlugin'

    DEFAULT_EXTENTIONS = ['.mrc', '.rec', '.ali']

    descriptor_keys = ['']

    def __call__(self, path, index_t):

        #with mrc.fileMRC as mrc1:
        #    im1 = mrc1.getSlice(0,index_t)
        
        mrc1 = mrc.fileMRC(path)
        im1 = mrc1.getSlice(index_t)
        del mrc1
        
        return im1
        
    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            num_t = cls.num_t(path)
            num_z = cls.num_z(path)
            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path, index_t))

    @staticmethod
    def num_z(path):
        '''MRC files can only be 3D. Use num_t for 3D files.
        
        Returns 1 always
        '''
        
        return 1

    @staticmethod
    def num_t(path):
        '''The number of slices in the first dimension (C-ordering)
        
        '''
        #with mrc.fileMRC(path) as mrc1:
        #    out = mrc1.dataSize[0]
        
        mrc1 = mrc.fileMRC(path)
        out = mrc1.dataSize[0]
        return out
        
    @classmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(cls, path):
        with mrc.fileMRC(path) as mrc1:
            
            #Save most useful metaData
            metaData = {}
            metaData['file type'] = 'mrc'
            if hasattr(mrc1,'FEIinfo'):
                #add in the special FEIinfo if it exists
                metaData.update(mrc1.FEIinfo) 
            
            metaData['pixelSize'] = mrc1.voxelSize #the pixel sizes
            
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
