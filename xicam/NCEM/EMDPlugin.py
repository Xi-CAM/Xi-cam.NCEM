'''Part of the NCEM plugin for Xicam to read and display EMD (Berkeely style) EMD files.
THey are primarily used to store transmission electron microscopy data and metadata.

EMD files are a specially formatted type of HDF5 file. THere are two types of files. 
One is a "berkeley EMD file" described at www.emdatasets.com. The second is written
by Thermo Fischer (formerly FEI) Velox software. This file attempts Berkeley EMD file reading
and then Velox file reading.

The files are parsed using the ncempy.io.fileEMD class.

Notes:
    - Currently only loads the first data set in an EMD file.
    - Supports 2D and 3D data sets (3D as C-style ordering [t,y,x].
    - 4D datasets are loaded with the first index (C-ordering set to 0.

'''

import json
import functools

from xicam.plugins.datahandlerplugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc
from xicam.core import msg

from numpy import where as npwhere
from ncempy.io import emd #EMD BErkeley datasets
from ncempy.io import emdVelox #EMD Velox datasets

import h5py #for EMD Velox data sets
import h5py_cache #for EMD velox files to improve reading performance

class EMDPlugin(DataHandlerPlugin):
    name = 'EMDPlugin'

    DEFAULT_EXTENTIONS = ['.emd']

    descriptor_keys = ['object_keys']

    def __call__(self, index_t, dsetNum=0):
        im1 = None
        if not self.veloxFlag:
            #Berkeley EMD
            dataset0 = self.emd1.list_emds[dsetNum]['data'] #get the dataset in the first group found
            if dataset0.ndim == 2:
                im1 = dataset0
            elif dataset0.ndim == 3:
                im1 = dataset0[index_t,:,:]
            elif dataset0.ndim == 4:
                im1 = dataset0[index_t,0,:,:]
        else:
            #Velox EMD
            dataset0 = self.emd1.list_data[dsetNum]['Data']
            if dataset0.ndim == 2:
                im1 = dataset0
            elif dataset0.ndim == 3:
                im1 = dataset0[:,:,index_t]
        return im1

    def __init__(self, path):
        super(EMDPlugin, self).__init__()
        self._metadata = None
        self.path = path

        self.veloxFlag = False
        #First try to open as EMD Berkeley file
        try:
            self.emd1 = emd.fileEMD(path,readonly=True)
            dataset0 = self.emd1.list_emds[0]['data'] #get the dataset in the first group found
        except IndexError:
            msg.logMessage('EMD: No emd_dataset tags detected.')
            self.veloxFlag = True
        except:
            raise

        #Open as Velox EMD file. Only supports 1 data set currently
        if self.veloxFlag:
            try:
                self.emd1 = emdVelox.fileEMDVelox(path)
                dataset0 = self.emd1.list_data[0]['Data']
            except KeyError:
                msg.logMessage('EMD: No Velox Image group detected.')
                raise
            except IndexError:
                msg.logMessage('EMD: No Velox image detected.')
                raise
            except:
                raise

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            # Grab the metadata by temporarily instanciating the class and retrieving the metadata.
            # cls().metadata is not part of spec, but implemented here as a special
            # NOT NEEDED FOR EMDs.
            metadata = cls.metadata(path)

            num_t = cls.num_t(metadata)
            num_z = 1
                        
            for index_z in range(num_z):
                for index_t in range(num_t):
                    yield embedded_local_event_doc(descriptor_uid,
                                                   'primary',
                                                   cls,
                                                   (path,),
                                                   {'index_t': index_t})

    @staticmethod
    def num_z(metadata):
        '''Limit to only 3D datasets.
        
        Returns 1 always
        '''

        return 1

    @staticmethod
    def num_t(metadata):
        '''The number of slices in the first dimension (C-ordering) for Berkeley data sets
        OR
        The number of slices in the last dimension (F-ordering) for Velox data sets
        
        '''
        if len(metadata['shape']) < 3:
            out = 1
        else:
            if not metadata['veloxFlag']:
                #EMD Berkeley
                out = metadata['shape'][0] #Velox files are written incorrectly using Fortran ordering
            else:
                #EMD Velox
                out = metadata['shape'][-1]

        return out

    @classmethod
    def parseDataFile(cls, path):
        metaData = cls.metadata(path)

        metaData['FileName'] = path

        return metaData

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def metadata(path):

        metaData = {}
        metaData['veloxFlag'] = False

        #First try to open as EMD Berkeley file
        try:
            #EMD Berkeley
            emd1 = emd.fileEMD(path,readonly=True)
            dataGroup = emd1.list_emds[0]
            dataset0 = dataGroup['data'] #get the dataset in the first group found

            try:
                metaData.update(emd1.file_hdl['/user'].attrs)
            except:
                pass
            try:
                metaData.update(emd1.file_hdl['/microscope'].attrs)
            except:
                pass
            try:
                metaData.update(emd1.file_hdl['/sample'].attrs)
            except:
                pass
            try:
                metaData.update(emd1.file_hdl['/comments'].attrs)
            except:
                pass
            try:
                metaData.update(emd1.file_hdl['/stage'].attrs)
            except:
                pass
                
            if dataset0.ndim == 2:
                dimY = dataGroup['dim1']
                dimX = dataGroup['dim2']
            elif dataset0.ndim == 3:
                dimY = dataGroup['dim2']
                dimX = dataGroup['dim3']
            elif dataset0.ndim == 4:
                dimY = dataGroup['dim3']
                dimX = dataGroup['dim4']

            #Store the X and Y pixel size, offset and unit
            metaData['PhysicalSizeX'] = dimX[1] - dimX[0]
            metaData['PhysicalSizeXOrigin'] = dimX[0]
            metaData['PhysicalSizeXUnit'] = dimX.attrs['units'].decode('utf-8')
            metaData['PhysicalSizeY'] = dimY[1] - dimY[0]
            metaData['PhysicalSizeYOrigin'] = dimY[0]
            metaData['PhysicalSizeYUnit'] = dimY.attrs['units'].decode('utf-8')

            metaData['shape'] = dataset0.shape

        except IndexError:
            metaData['veloxFlag'] = True
        except:
            raise

        #Open as Velox EMD file. Only supports 1 data set currently
        if metaData['veloxFlag']:
            emd1 = emdVelox.fileEMDVelox(path)
            dataGroup = emd1.list_data[0]
            dataset0 = dataGroup['Data']

            #Convert JSON metadata to dict
            mData = emd1.list_data[0]['Metadata'][:,0]
            validMetaDataIndex = npwhere(mData > 0) #find valid metadata
            mData = mData[validMetaDataIndex].tostring() #change to string
            mDataS = json.loads(mData.decode('utf-8','ignore')) #load UTF-8 string as JSON and output dict
            try:
                #Store the X and Y pixel size, offset and unit
                metaData['PhysicalSizeX'] = float(mDataS['BinaryResult']['PixelSize']['width'])
                metaData['PhysicalSizeXOrigin'] = float(mDataS['BinaryResult']['Offset']['x'])
                metaData['PhysicalSizeXUnit'] = mDataS['BinaryResult']['PixelUnitX']
                metaData['PhysicalSizeY'] = float(mDataS['BinaryResult']['PixelSize']['height'])
                metaData['PhysicalSizeYOrigin'] = float(mDataS['BinaryResult']['Offset']['y'])
                metaData['PhysicalSizeYUnit'] = mDataS['BinaryResult']['PixelUnitY']
            except:
                msg.logMessage('EMD: Velox metadata parsing failed.')
                raise

            metaData.update(mDataS)

            metaData['shape'] = dataset0.shape
        return metaData
    
    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})

    @classmethod
    def getDescriptorDocs(cls, paths, start_uid, descriptor_uid):
        metadata = cls.parseTXTFile(paths[0])
        metadata.update(cls.parseDataFile(paths[0]))
        metadata.update({'object_keys': {'Device0': ['Device name0']}})  # TODO: add device detection

        # TODO: Check with Peter if all keys should go in the descriptor, or if some should go in the events
        # metadata = dict([(key, metadata.get(key, None)) for key in getattr(cls, 'descriptor_keys', [])])
        yield descriptor_doc(start_uid, descriptor_uid, metadata=metadata)
