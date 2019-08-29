from xicam.plugins.datahandlerplugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
#import uuid
import functools
#from pathlib import Path
from xicam.core import msg
from ncempy.io import mrc


class MRCPlugin(DataHandlerPlugin):
    name = 'MRCPlugin'

    DEFAULT_EXTENTIONS = ['.mrc', '.rec', '.ali','.st']

    descriptor_keys = ['object_keys']

    def __call__(self, index_z, index_t):
        im1 = self.mrc.getSlice(index_t)
        #for ii in range(1,5):
        #    im = self.mrc.getSlice(index_t+ii)
        #    im1 += im
        return im1

    def __init__(self, path):
        super(MRCPlugin, self).__init__()
        self._metadata = None
        self.path = path
        self.mrc = mrc.fileMRC(self.path)

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        
        for path in paths:
            # Grab the metadata by temporarily instanciating the class and retrieving the metadata.
            # cls().metadata is not part of spec, but implemented here as a special case
            metadata = cls.metadata(path)

            num_t = cls.num_t(path)
            num_z = 1

            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path,),
                                                   {'index_z': index_z, 'index_t': index_t})

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
        with mrc.fileMRC(path) as mrc1:
            out = mrc1.dataSize[0]

        return out

    @classmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(cls, path):
        with mrc.fileMRC(path) as mrc1:
            # Save most useful metaData
            metaData = {}
            if hasattr(mrc1, 'FEIinfo'):
                # add in the special FEIinfo if it exists
                metaData.update(mrc1.FEIinfo)

            #Store the X and Y pixel size, offset and unit
            metaData['PhysicalSizeX'] = mrc1.voxelSize[2]*1e-10 #change Angstroms to meters
            metaData['PhysicalSizeXOrigin'] = 0
            metaData['PhysicalSizeXUnit'] = 'm'
            metaData['PhysicalSizeY'] = mrc1.voxelSize[1]*1e-10 #change Angstroms to meters
            metaData['PhysicalSizeYOrigin'] = 0
            metaData['PhysicalSizeYUnit'] = 'm'
            
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
        # metadata = dict([(key, metadata.get(key, None)) for key in getattr(cls, 'descriptor_keys', [])])
        yield descriptor_doc(start_uid, descriptor_uid, metadata=metadata)

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def metadata(path):

        with mrc.fileMRC(path) as mrc1:
            pass
        metaData = mrc1.dataOut #meata data information from the mrc header

        # TODO: The lines below would be better to go in parseTXTFile.
        rawtltName = os.path.splitext(path)[0] + '.rawtlt'
        if os.path.isfile(rawtltName):
            with open(rawtltName,'r') as f1:
                tilts = map(float,f1)
            metaData['tilt angles'] = tilts
        FEIparameters = os.path.splitext(path)[0] + '.txt'
        if os.path.isfile(FEIparameters):
            with open(FEIparameters,'r') as f2:
                lines = f2.readlines()
            pp1 = list([ii[18:].strip().split(':')] for ii in lines[3:-1])
            pp2 = {}
            for ll in pp1:
                try:
                    pp2[ll[0]] = float(ll[1])
                except:
                    pass #skip lines with no data
            metaData.update(pp2)
        
        
        return metaData
