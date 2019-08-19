import functools

from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc
from xicam.core import msg

from ncempy.io import dm
## For testing locally with ncempy development code
#import sys
#sys.path.append(r'C:\Users\Peter.000\Documents\scripting\openNCEMgh\ncempy\io')
#import dm

class DMPlugin(DataHandlerPlugin):
    name = 'DMPlugin'

    DEFAULT_EXTENTIONS = ['.dm3', '.dm4']

    descriptor_keys = ['object_keys']


    def __call__(self, index_z, index_t):
        im1 = self.dm0.getSlice(0, index_t, sliceZ2=index_z)  # Most DM files have only 1 dataset
        return im1['data']

    def __init__(self, path):
        super(DMPlugin, self).__init__()
        self._metadata = None
        self.path = path
        self.dm0 = dm.fileDM(self.path,on_memory = True)

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            # Grab the metadata by temporarily instanciating the class and retrieving the metadata.
            # cls().metadata is not part of spec, but implemented here as a special case
            metadata = cls.metadata(path)

            num_z = cls.num_z(path)
            num_t = cls.num_t(path)
            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path,),
                                                   {'index_z': index_z, 'index_t': index_t})

    @staticmethod
    def num_z(path):
        '''The number of slices along axis 1 (start at 0) (C-ordering)
        for 4D data sets. Not used for 3D data sets
        
        
        Only used for 4D data sets
        '''
        with dm.fileDM(path,on_memory = True) as dm1:
            if dm1.thumbnail:
                out = dm1.zSize2[1]
            else:
                out = dm1.zSize2[0]
        return out

    @staticmethod
    def num_t(path):
        '''The number of slices in the first dimension (C-ordering) for 3D
        datasets
        
        This is the number of slices along the "Z" axis. For a 3D volume
        this is is a slice long Z. For an image stack this is the requested
        image in the stack.
        
        '''
        with dm.fileDM(path,on_memory = True) as dm1:
            if dm1.thumbnail:
                out = dm1.zSize[1]
            else:
                out = dm1.zSize[0]
        return out
        
    @classmethod
    def parseDataFile(path):
        return cls.metadata(path)
    
    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})

    @classmethod
    def getDescriptorDocs(cls, paths, start_uid, descriptor_uid):
        md = cls.parseTXTFile(paths[0])
        md.update(cls.metadata(paths[0]))
        md.update({'object_keys': {'Unknown Device': ['Unknown Device']}})  # TODO: add device detection

        # TODO: Check with Peter if all keys should go in the descriptor, or if some should go in the events
        # md = dict([(key, md.get(key, None)) for key in getattr(cls, 'descriptor_keys', [])])
        yield descriptor_doc(start_uid, descriptor_uid, metadata=md)

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def metadata(path):
        metaData = {}
        with dm.fileDM(path,on_memory = True) as dm1:
            # Save most useful metaData
            
            #Only keep the most useful tags as meta data
            for kk, ii in dm1.allTags.items():
                # Most useful starting tags
                prefix1 = 'ImageList.{}.ImageTags.'.format(dm1.numObjects)
                prefix2 = 'ImageList.{}.ImageData.'.format(dm1.numObjects)
                pos1 = kk.find(prefix1)
                pos2 = kk.find(prefix2)
                if pos1 > -1:
                    sub = kk[pos1 + len(prefix1):]
                    metaData[sub] = ii
                elif pos2 > -1:
                    sub = kk[pos2 + len(prefix2):]
                    metaData[sub] = ii

                # Remove unneeded keys
                for jj in list(metaData):
                    if jj.find('frame sequence') > -1:
                        del metaData[jj]
                    elif jj.find('Private') > -1:
                        del metaData[jj]
                    elif jj.find('Reference Images') > -1:
                        del metaData[jj]
                    elif jj.find('Frame.Intensity') > -1:
                        del metaData[jj]
                    elif jj.find('Area.Transform') > -1:
                        del metaData[jj]
                    elif jj.find('Parameters.Objects') > -1:
                        del metaData[jj]
                    elif jj.find('Device.Parameters') > -1:
                        del metaData[jj]
        
            #Store the X and Y pixel size, offset and unit
            metaData['PhysicalSizeX'] = metaData['Calibrations.Dimension.1.Scale']
            metaData['PhysicalSizeXOrigin'] = metaData['Calibrations.Dimension.1.Origin']
            metaData['PhysicalSizeXUnit'] = metaData['Calibrations.Dimension.1.Units']
            metaData['PhysicalSizeY'] = metaData['Calibrations.Dimension.2.Scale']
            metaData['PhysicalSizeYOrigin'] = metaData['Calibrations.Dimension.2.Origin']
            metaData['PhysicalSizeYUnit'] = metaData['Calibrations.Dimension.2.Units']
            
            metaData['FileName'] = path

        return metaData
