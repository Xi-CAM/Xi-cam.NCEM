import os
import functools
import time
import dask
import dask.array as da
from pathlib import Path

import event_model

from ncempy.io import ser


def _num_t(metadata):
    """ The number of data sets in the ser file. SER files are always laid out as a 'series'
    of 1D or 2D datasets. Thus, you need to retrieve each data set in the series separately.

    2D data sets:
    For series of 2D datasets this is a layout of X,Y for each data set

    1D data sets (unuspported!)
    For series of 1D data sets (spectra) this is a layout of 1 spectra at each position
    in a 1D or 2D raster.

    Note: Each data set can have a different X-Y size. Its rare but possible.
    """
    # TODO: Alert Peter Ercius that the type returned by metadata['ValidNumberElements should be `int`
    # TODO: Not sure why there's a conditional here?
    if metadata['DataTypeID'] == 16674:
        # 2D data sets (images)
        return int(metadata['ValidNumberElements'])
    elif metadata['DataTypeID'] == 16672:
        # 1D data sets (currently unsupported)
        return int(metadata['ValidNumberElements'])

    return None


@functools.lru_cache(maxsize=10, typed=False)
def _metadata(path):
    with ser.fileSER(path) as ser1:
        data, metaData = ser1.getDataset(0)  # have to get 1 image and its meta data

        # Add extra meta data from the EMI file if it exists
        if ser1._emi is not None:
            metaData.update(ser1._emi)

    metaData.update(ser1.head)  # some header data for the ser file

    # Clean the dictionary
    for k, v in metaData.items():
        if isinstance(v, bytes):
            metaData[k] = v.decode('UTF8')

    # Store the X and Y pixel size, offset and unit
    try:
        metaData['PhysicalSizeX'] = metaData['Calibration'][0]['CalibrationDelta']
        metaData['PhysicalSizeXOrigin'] = metaData['Calibration'][0]['CalibrationOffset']
        metaData['PhysicalSizeXUnit'] = 'm'  # always meters
        metaData['PhysicalSizeY'] = metaData['Calibration'][1]['CalibrationDelta']
        metaData['PhysicalSizeYOrigin'] = metaData['Calibration'][1]['CalibrationOffset']
        metaData['PhysicalSizeYUnit'] = 'm'  # always meters
    except:
        metaData['PhysicalSizeX'] = 1
        metaData['PhysicalSizeXOrigin'] = 0
        metaData['PhysicalSizeXUnit'] = ''
        metaData['PhysicalSizeY'] = 1
        metaData['PhysicalSizeYOrigin'] = 0
        metaData['PhysicalSizeYUnit'] = ''

    metaData['FileName'] = path

    return metaData


def _get_slice(path, t):
    with ser.fileSER(path) as ser_obj:
        return ser_obj.getDataset(t)[0]


def ingest_NCEM_SER(paths):
    assert len(paths) == 1
    path = paths[0]

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = metadata = _metadata(path)
    start_doc.update(run_bundle.start_doc)
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    yield 'start', start_doc

    #ser_handle = ser.fileSER(path)
    num_t = _num_t(metadata)
    first_frame = _get_slice(path, 0)
    shape = first_frame.shape
    dtype = first_frame.dtype

    delayed_get_slice = dask.delayed(_get_slice)
    dask_data = da.stack([da.from_delayed(delayed_get_slice(path, t), shape=shape, dtype=dtype)
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


if __name__ == "__main__":
    output = list(ingest_NCEM_SER([r"C:\Users\linol\Data/10_series_1.ser"]))
    print(output)
