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
        im1 = aa.getDataset(0) #Most DM files have only 1 dataset
        #return im1['data']
        if im1['data'].ndim == 2:
            #2D image
            return im1['data']
        elif im1['data'].ndim == 3:
            #3D data set. Volume or image stack
            return im1['data'][index_t,:,:]
        elif im1['data'].ndim == 4:
            #Not fully implemented yet. 4D DM4 files are written in
            #written as [kx,ky,Y,X]. We want 
            return im1['data'][index_z,index_t,:,:]
        
    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            for index_z in range(cls.num_z(path)):
                for index_t in range(cls.num_t(path)):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path, index_z, index_t))

    @staticmethod
    def num_z(path):
        '''The number of slizes along axis 2 (start at 0) (C-ordering)
        for 4D data sets. Not used for 3D data sets
        
        
        Only used for 4D data sets
        '''
        f = dm.fileDM(path)
        f.parseHeader()
        return f.zSize2[1] #use zSize2[1] rather than [0] to skip the thumbnail

    @staticmethod
    def num_t(path):
        '''The number of slices in the first dimension (C-ordering) for 3D
        datasets
        
        This is the number of slices along the "Z" axis. For a 3D volume
        this is is a slize long Z. For an image stack this is the requested
        image in the stack.
        
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