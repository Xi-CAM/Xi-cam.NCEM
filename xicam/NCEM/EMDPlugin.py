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

from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import json
import functools
from xicam.core import msg
import numpy as np
from ncempy.io import emd #EMD BErkeley datasets
import h5py #for EMD Velox data sets

class EMDPlugin(DataHandlerPlugin):
    name = 'EMDPlugin'

    DEFAULT_EXTENTIONS = ['.emd']

    descriptor_keys = ['']

    def __call__(self, path, index_t):
        veloxFlag = False
        im1 = None
        
        #First try to open as EMD Berkeley file
        try:
            with emd.fileEMD(path,readonly=True) as emd1:
                dataset0 = emd1.list_emds[0]['data'] #get the dataset in the first group found
                
                if dataset0.ndim == 2:
                    im1 = dataset0['data']
                elif dataset0.ndim == 3:
                    im1 = dataset0['data'][index_t,:,:]
                elif dataset0.ndim == 4:
                    im1 = dataset0['data'][0,index_t,:,:]
                else:
                    msg.logMessage('EMD: Only 1D-4D EMD Berkeley data sets are supported.')
        except IndexError:
            im1 = None
            msg.logMessage('EMD: No emd_dataset tags detected.')
            veloxFlag = True
        
        #Open as Velox EMD file. Only supports 1 data set currently
        if veloxFlag:
            try:
                with h5py.File(path,'r') as f1:
                    f1Im = f1['Data/Image']
                    #Get all of the groups in the Image group
                    dsetGroups = list(f1['Data/Image'].values())
                    
                    im1 = dsetGroups[0]['Data'][:,:,index_t] #Velox data is written incorrectly with Fortran ordering
            except KeyError:
                msg.logMessage('EMD: No Velox Image group detected.')
                raise
            except IndexError:
                msg.logMessage('EMD: No Velox image detected.')
                raise
            except:
                raise
        
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
        '''Limit to only 3D datasets.
        
        Returns 1 always
        '''

        return 1

    @staticmethod
    def num_t(path):
        '''The number of slices in the first dimension (C-ordering) for Berkeley data sets
        OR
        The number of slices in the last dimension (F-ordering) for Velox data sets
        
        '''
        veloxFlag = False
        try:
            with emd.fileEMD(path) as emd1:
                dataset0 = emd1.list_emds[0]['data'] #get the dataset in the first group found

                out = dataset0.shape[0]
        except IndexError:
            veloxFlag = True
        except:
            raise
        
        if veloxFlag:
            try:
                with h5py.File(path,'r') as f1:
                    f1Im = f1['Data/Image']
                    #Get all of the groups in the Image group
                    dsetGroups = list(f1['Data/Image'].values())
                    out = dsetGroups[0]['Data'].shape[-1] #Velox files are written incorrectly using Fortran ordering
            except:
                raise
                out = 0
        return out

    @classmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(cls, path):
        metaData = {}
        veloxFlag = False
        
        #Open as Berkelely EMD file
        try:
            with emd.fileEMD(path) as emd1:
                dataset0 = emd1.list_emds[0]
                
                # Save most useful metaData
                metaData['file type'] = 'emd berkeley'
                
                try:
                    metaData.update(emd1.file_hdl['/user'].attrs)
                try:
                    metaData.update(emd1.file_hdl['/microscope'].attrs)
                try:
                    metaData.update(emd1.file_hdl['/sample'].attrs)
                try:
                    metaData.update(emd1.file_hdl['/comments'].attrs)
                
                if dataset0.ndim == 2:
                    dimY = emd1.list_emds[0]['dim1']
                    dimX = emd1.list_emds[0]['dim2']
                elif dataset0.ndim == 3:
                    dimY = emd1.list_emds[0]['dim2']
                    dimX = emd1.list_emds[0]['dim3']

                #Store the X and Y pixel size, offset and unit
                metaData['PhysicalSizeX'] = dimX[1] - dimX[0]
                metaData['PhysicalSizeXOrigin'] = dimX[0]
                metaData['PhysicalSizeXUnit'] = dimX.attrs['units']
                metaData['PhysicalSizeY'] = dimY[1] - dimY[0]
                metaData['PhysicalSizeYOrigin'] = dimY[0]
                metaData['PhysicalSizeYUnit'] = dimY.attrs['units']
            
        except IndexError:
            msg.logMessage('EMD: No emd_dataset tags detected.')
            veloxFlag = True
        except:
            raise
            
        #Open as Velox file
        # This will eventually be moved to ncempy.io
        if veloxFlag:
            try:
                with h5py.File(path,'r') as f1:
                    f1Im = f1['Data/Image']
                    #Get all of the groups in the Image group
                    dsetGroups = list(f1['Data/Image'].values())
                    
                    #Convert JSON metadata to dict
                    mData = dsetGroups[0]['Metadata'][:,0]
                    validMetaDataIndex = np.where(mData > 0) #find valid metadata
                    mData = mData[validMetaDataIndex].tostring() #change to string
                    jj = json.loads(mData.decode('utf-8','ignore')) #load UTF-8 string as JSON and output dict
                    metaData.update(jj)
                    
                    #Store the X and Y pixel size, offset and unit
                    metaData['PhysicalSizeX'] = float(jj['BinaryResult']['PixelSize']['width'])
                    metaData['PhysicalSizeXOrigin'] = float(jj['BinaryResult']['Offset']['x'])
                    metaData['PhysicalSizeXUnit'] = jj['BinaryResult']['PixelPixelUnitX']
                    metaData['PhysicalSizeY'] = float(jj['BinaryResult']['PixelSize']['height'])
                    metaData['PhysicalSizeYOrigin'] = float(jj['BinaryResult']['Offset']['y'])
                    metaData['PhysicalSizeYUnit'] = jj['BinaryResult']['PixelPixelUnitY']
            except:
                msg.logMessage('EMD: Velox meta data parsing failed.')
                raise
        
        metaData['FileName'] = path
        
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
