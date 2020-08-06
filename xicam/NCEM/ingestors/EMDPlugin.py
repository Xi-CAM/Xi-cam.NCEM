""" Part of the NCEM plugin for Xicam to read and display EMD (Berkeley style) EMD files.
They are primarily used to store transmission electron microscopy data and metadata.

EMD files are a specially formatted type of HDF5 file. There are two types of files.
One is a "Berkeley EMD file" described at www.emdatasets.com. The second is written
by Thermo Fischer (formerly FEI) Velox software. This file attempts to read the files as a Berkeley EMD
and then a Velox file.

The files are parsed using the ncempy.io.fileEMD or the ncempy.io.fileEMDVelox class.

Notes:
    - Currently only loads the first data set in an EMD file.
    - Supports 2D and 3D data sets (3D as C-style ordering) [t,y,x].
    - 4D datasets are loaded with the first index (C-ordering) set to 0.

"""

import json
import functools
import time
import dask
import dask.array as da
from pathlib import Path
import numpy as np
from collections.abc import Iterable
import numbers

import event_model
from xicam.core import msg

from numpy import where as npwhere
from numpy import ndarray as ndarray
from ncempy.io import emd  # EMD Berkeley datasets
from ncempy.io import emdVelox  # EMD Velox datasets


def _guess_type(value):
    if isinstance(value, str):
        return "string"
    elif isinstance(value, numbers.Real):
        return "number"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, numbers.Integral):
        return "integer"
    # elif isinstance(value, Iterable):  # TODO: Ask about this in the coalition call; somehow this is breaking xarray's coords
    #     return "array"
    else:
        return None


def _num_t(emd_obj, dset_num=0):
    """ The number of slices in the first dimension (C-ordering) for Berkeley data sets
    OR
    The number of slices in the last dimension (F-ordering) for Velox data sets

    """

    dataGroup = emd_obj.list_emds[dset_num]
    dataset0 = dataGroup['data']
    shape = dataset0.shape

    if len(shape) < 3:
        out = 1
    else:
        # EMD Berkeley
        out = shape[0]  # Velox files are written incorrectly using Fortran ordering

    return out


def _num_datasets(emd_obj):
    return len(emd_obj.list_emds)


def _get_slice(emd_obj, t, dset_num=0):
    dataset0 = emd_obj.list_emds[dset_num]['data']  # get the dataset in the first group found
    if dataset0.ndim == 2:
        im1 = dataset0
    elif dataset0.ndim == 3:
        im1 = dataset0[t, :, :]
    elif dataset0.ndim == 4:
        im1 = dataset0[t, 0, :, :]
    return np.asarray(im1)


# Modify types if needed
def _cleandict(md):
    for k, v in md.items():
        if isinstance(v, dict):
            _cleandict(v)
        elif isinstance(v, bytes):
            md[k] = v.decode('UTF8')
        elif isinstance(v, ndarray):
            md[k] = tuple(v)


@functools.lru_cache(maxsize=10, typed=False)
def _metadata(path):  # parameterized by path rather than emd_obj so that hashing lru hashing resolves easily

    metaData = {}
    metaData['veloxFlag'] = False

    metaData['FileName'] = path

    # EMD Berkeley
    emd_obj = emd.fileEMD(path, readonly=True)

    try:
        metaData['user'] = {}
        metaData['user'].update(emd_obj.file_hdl['/user'].attrs)
    except:
        pass
    try:
        metaData['microscope'] = {}
        metaData['microscope'].update(emd_obj.file_hdl['/microscope'].attrs)
    except:
        pass
    try:
        metaData['sample'] = {}
        metaData['sample'].update(emd_obj.file_hdl['/sample'].attrs)
    except:
        pass
    try:
        metaData['comments'] = {}
        metaData['comments'].update(emd_obj.file_hdl['/comments'].attrs)
    except:
        pass
    try:
        metaData['stage'] = {}
        metaData['stage'].update(emd_obj.file_hdl['/stage'].attrs)
    except:
        pass

    _cleandict(metaData)

    return metaData


def _dset_names(emd_obj):
    return [emd_obj.list_emds[device_index].name.split('/')[-1] for device_index in range(_num_datasets(emd_obj))]



@functools.lru_cache(maxsize=10, typed=False)
def _metadata_from_dset(path, dset_num=0):  # parameterized by path rather than emd_obj so that hashing lru hashing resolves easily

    metaData = {}
    metaData['veloxFlag'] = False

    # EMD Berkeley
    emd_obj = emd.fileEMD(path, readonly=True)
    dataGroup = emd_obj.list_emds[dset_num]
    dataset0 = dataGroup['data']  # get the dataset in the first group found

    try:
        name = dataGroup.name.split('/')[-1]
        metaData[name] = {}
        metaData[name].update(dataGroup.attrs)
    except:
        pass

    # Get the dim vectors
    dims = emd_obj.get_emddims(dataGroup)
    if dataset0.ndim == 2:
        dimZ = None
        dimY = dims[0]  # dataGroup['dim1']
        dimX = dims[1]  # dataGroup['dim2']
    elif dataset0.ndim == 3:
        dimZ = dims[0]
        dimY = dims[1]  # dataGroup['dim2']
        dimX = dims[2]  # dataGroup['dim3']
    elif dataset0.ndim == 4:
        dimZ = dims[1]
        dimY = dims[2]  # dataGroup['dim3']
        dimX = dims[3]  # dataGroup['dim4']
    else:
        dimZ = None
        dimY = None
        dimX = None

    # Store the X and Y pixel size, offset and unit
    try:
        metaData['PhysicalSizeX'] = dimX[0][1] - dimX[0][0]
        metaData['PhysicalSizeXOrigin'] = dimX[0][0]
        metaData['PhysicalSizeXUnit'] = dimX[2].replace('_', '')
        metaData['PhysicalSizeY'] = dimY[0][1] - dimY[0][0]
        metaData['PhysicalSizeYOrigin'] = dimY[0][0]
        metaData['PhysicalSizeYUnit'] = dimY[2].replace('_', '')
        # metaData['PhysicalSizeZ'] = dimZ[0][1] - dimZ[0][0]
        # metaData['PhysicalSizeZOrigin'] = dimZ[0][0]
        # metaData['PhysicalSizeZUnit'] = dimZ[2]
    except:
        metaData['PhysicalSizeX'] = 1
        metaData['PhysicalSizeXOrigin'] = 0
        metaData['PhysicalSizeXUnit'] = ''
        metaData['PhysicalSizeY'] = 1
        metaData['PhysicalSizeYOrigin'] = 0
        metaData['PhysicalSizeYUnit'] = ''

    metaData['shape'] = dataset0.shape

    _cleandict(metaData)

    return metaData


def ingest_NCEM_EMD(paths):
    assert len(paths) == 1
    path = paths[0]

    emd_handle = emd.fileEMD(path, readonly=True)

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = run_bundle.start_doc
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    metadata = _metadata(path)

    metadata.update(start_doc)
    start_doc = metadata
    yield 'start', start_doc

    for device_index, device_name in enumerate(_dset_names(emd_handle)):

        num_t = _num_t(emd_handle, dset_num=device_index)
        first_frame = _get_slice(emd_handle, 0, dset_num=device_index)
        shape = first_frame.shape
        dtype = first_frame.dtype

        delayed_get_slice = dask.delayed(_get_slice)
        dask_data = da.stack([da.from_delayed(delayed_get_slice(emd_handle, t, dset_num=device_index), shape=shape, dtype=dtype)
                              for t in range(num_t)])

        # Compose descriptor
        source = 'NCEM'
        frame_data_keys = {'raw': {'source': source,
                                   'dtype': 'number',
                                   'shape': (num_t, *shape)}}

        frame_stream_name = f'primary_{device_name}'
        stream_metadata = _metadata_from_dset(path, dset_num=device_index)
        configuration = {key: {"data": {key: value},
                               "timestamps": {key: time.time()},
                               "data_keys": {key: {"source": path,
                                                   "dtype": _guess_type(value),
                                                   "shape": [],
                                                   "units": "",
                                                   #"related_value": 0, ... # i.e. soft limits, precision
                                                   }}}
                         for key, value in stream_metadata.items() if _guess_type(value)}

        frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                            name=frame_stream_name,
                                                            configuration=configuration
                                                            )
        yield 'descriptor', frame_stream_bundle.descriptor_doc

        # NOTE: Resource document may be meaningful in the future. For transient access it is not useful
        # # Compose resource
        # resource = run_bundle.compose_resource(root=Path(path).root, resource_path=path, spec='NCEM_DM', resource_kwargs={})
        # yield 'resource', resource.resource_doc

        # Compose datum_page
        # z_indices, t_indices = zip(*itertools.product(z_indices, t_indices))
        # datum_page_doc = resource.compose_datum_page(datum_kwargs={'index_z': list(z_indices), 'index_t': list(t_indices)})
        # datum_ids = datum_page_doc['datum_id']
        # yield 'datum_page', datum_page_doc

        yield 'event', frame_stream_bundle.compose_event(data={'raw': dask_data},
                                                         timestamps={'raw': time.time()})

    yield 'stop', run_bundle.compose_stop()


def _get_slice_velox(emd_obj, t, dset_num=0):
    # Velox EMD
    dataset0 = emd_obj.list_data[dset_num]['Data']
    if dataset0.ndim == 2:
        im1 = dataset0
    elif dataset0.ndim == 3:
        im1 = dataset0[:, :, t]
    return im1


def _num_t_velox(emd_obj):
    """ The number of slices in the first dimension (C-ordering) for Berkeley data sets
    OR
    The number of slices in the last dimension (F-ordering) for Velox data sets

    """

    dataGroup = emd_obj.list_data[0]
    dataset0 = dataGroup['Data']
    shape = dataset0.shape

    if len(shape) < 3:
        out = 1
    else:
        # EMD Velox
        out = shape[-1]

    return out


@functools.lru_cache(maxsize=10, typed=False)
def _metadata_velox(path):  # parameterized by path rather than emd_obj so that hashing lru hashing resolves easily

    metaData = {}
    metaData['veloxFlag'] = True

    metaData['FileName'] = path

    emd_obj = emdVelox.fileEMDVelox(path)
    dataGroup = emd_obj.list_data[0]
    dataset0 = dataGroup['Data']

    # Convert JSON metadata to dict
    mData = emd_obj.list_data[0]['Metadata'][:, 0]
    validMetaDataIndex = npwhere(mData > 0)  # find valid metadata
    mData = mData[validMetaDataIndex].tostring()  # change to string
    mDataS = json.loads(mData.decode('utf-8', 'ignore'))  # load UTF-8 string as JSON and output dict
    try:
        # Store the X and Y pixel size, offset and unit
        metaData['PhysicalSizeX'] = float(mDataS['BinaryResult']['PixelSize']['width'])
        metaData['PhysicalSizeXOrigin'] = float(mDataS['BinaryResult']['Offset']['x'])
        metaData['PhysicalSizeXUnit'] = mDataS['BinaryResult']['PixelUnitX']
        metaData['PhysicalSizeY'] = float(mDataS['BinaryResult']['PixelSize']['height'])
        metaData['PhysicalSizeYOrigin'] = float(mDataS['BinaryResult']['Offset']['y'])
        metaData['PhysicalSizeYUnit'] = mDataS['BinaryResult']['PixelUnitY']
    except:
        metaData['PhysicalSizeX'] = 1
        metaData['PhysicalSizeXOrigin'] = 0
        metaData['PhysicalSizeXUnit'] = ''
        metaData['PhysicalSizeY'] = 1
        metaData['PhysicalSizeYOrigin'] = 0
        metaData['PhysicalSizeYUnit'] = ''

    metaData.update(mDataS)

    metaData['shape'] = dataset0.shape

    return metaData


def ingest_NCEM_EMD_VELOX(paths):
    assert len(paths) == 1
    path = paths[0]

    emd_handle = emdVelox.fileEMDVelox(path)

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = run_bundle.start_doc
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    metadata = _metadata_velox(path)

    metadata.update(start_doc)
    start_doc = metadata
    yield 'start', start_doc

    num_t = _num_t_velox(emd_handle)
    first_frame = _get_slice_velox(emd_handle, 0)
    shape = first_frame.shape
    dtype = first_frame.dtype

    delayed_get_slice = dask.delayed(_get_slice_velox)
    dask_data = da.stack([da.from_delayed(delayed_get_slice(emd_handle, t), shape=shape, dtype=dtype)
                          for t in range(num_t)])

    # Compose descriptor
    source = 'NCEM'
    frame_data_keys = {'raw': {'source': source,
                               'dtype': 'number',
                               'shape': (num_t, *shape)}}
    frame_stream_name = 'primary'
    frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                        name=frame_stream_name,
                                                        # configuration=_metadata(path)
                                                        )
    yield 'descriptor', frame_stream_bundle.descriptor_doc

    # NOTE: Resource document may be meaningful in the future. For transient access it is not useful
    # # Compose resource
    # resource = run_bundle.compose_resource(root=Path(path).root, resource_path=path, spec='NCEM_DM', resource_kwargs={})
    # yield 'resource', resource.resource_doc

    # Compose datum_page
    # z_indices, t_indices = zip(*itertools.product(z_indices, t_indices))
    # datum_page_doc = resource.compose_datum_page(datum_kwargs={'index_z': list(z_indices), 'index_t': list(t_indices)})
    # datum_ids = datum_page_doc['datum_id']
    # yield 'datum_page', datum_page_doc

    yield 'event', frame_stream_bundle.compose_event(data={'raw': dask_data},
                                                     timestamps={'raw': time.time()})

    yield 'stop', run_bundle.compose_stop()


def emd_sniffer(path, first_bytes):
    if not Path(path).suffix.lower() == '.emd':
        return

    test_velox = False
    try:
        # Test for Berkeley EMD
        with emd.fileEMD(path, readonly=True) as emd1:
            if len(emd1.list_emds) > 0:
                return 'application/x-EMD'
            else:
                test_velox = True
    except OSError:
        # Not a HDF5 file
        return

    if test_velox:
        # Test for Velox
        with emdVelox.fileEMDVelox(path) as emd2:
            ver = emd2.file_hdl['Version'][0].decode('ASCII')
            if ver.find('Velox') > -1:
                return 'application/x-EMD-VELOX'
    else:
        return
