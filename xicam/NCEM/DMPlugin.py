from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path
from ncempy.io import dm


# TODO: ask peter to add __enter__ and 'with' support to NCEMPY's dm module

class DMPlugin(DataHandlerPlugin):
    name = 'DMPlugin'

    DEFAULT_EXTENTIONS = ['.dm3', '.dm4']

    def __call__(self, path, index_z, index_t):
        aa = dm.fileDM(path)
        aa.parseHeader()
        #Need if statements to deal with 2D and 3D and 4D datasets
        im1 = aa.getDataset(index_z) #should almost always have index_z=0
        if im1['data'].ndim == 2:
            return im1
        elif im1['data'].ndim == 3:
            return im1[:,:,index_t]
        elif im1['data'] = 4:
            #Not implemented yet. DM4 files are written in incorrectly written
            #in Fortran ordering
            return im1['data'][:,:,:,index_t]

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            for index_z in range(cls.num_z(path)):
                for index_t in range(cls.num_t(path)):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path, index_z, index_t))

    @staticmethod
    def num_z(path):
        '''The number of datasets in the DM file. Usually a thumbnail
        and the actual data. The thumbnail shoul dbe ignored
        
        '''
        f = dm.fileDM(path)
        f.parseHeader()
        return f.numObjects-1

    @staticmethod
    def num_t(path):
        '''The number of slices in the first dimension (C-ordering)
        
        This is for 3D datasets (volumes) and time series of focal series
        '''
        f = dm.fileDM(path)
        f.parseHeader()
        return f.zSize[1] #use zSize[1] rather than zSize[0] to ignore the thumbnail

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = dm.fileDM(path)
        md.parseHeader()
        return md.allTags

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})