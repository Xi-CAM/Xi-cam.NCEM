import functools
import event_model
from pathlib import Path
import time
import dask
import dask.array as da

from ncempy.io import dm


def _num_z(dm_obj):
    """ The number of slices along axis 1 (start at 0) (C-ordering)
    for 4D data sets. Not used for 3D data sets

    Only used for 4D data sets
    """

    if dm_obj.thumbnail:
        out = dm_obj.zSize2[1]
    else:
        out = dm_obj.zSize2[0]
    return int(out)


def _num_t(dm_obj):
    """ The number of slices in the first dimension (C-ordering) for 3D
    datasets

    This is the number of slices along the "Z" axis. For a 3D volume
    this is is a slice long Z. For an image stack this is the requested
    image in the stack.

    """

    if dm_obj.thumbnail:
        out = dm_obj.zSize[1]
    else:
        out = dm_obj.zSize[0]
    return int(out)


def get_slice(dm_obj, z, t):
    return dm_obj.getSlice(0, z, t)['data']


@functools.lru_cache(maxsize=10, typed=False)
def _metadata(path):
    metaData = {}
    with dm.fileDM(path, on_memory=True) as dm1:
        # Save most useful metaData

        # Only keep the most useful tags as meta data
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

        # Store the X and Y pixel size, offset and unit
        try:
            metaData['PhysicalSizeX'] = metaData['Calibrations.Dimension.1.Scale']
            metaData['PhysicalSizeXOrigin'] = metaData['Calibrations.Dimension.1.Origin']
            metaData['PhysicalSizeXUnit'] = metaData['Calibrations.Dimension.1.Units']
            metaData['PhysicalSizeY'] = metaData['Calibrations.Dimension.2.Scale']
            metaData['PhysicalSizeYOrigin'] = metaData['Calibrations.Dimension.2.Origin']
            metaData['PhysicalSizeYUnit'] = metaData['Calibrations.Dimension.2.Units']
        except:
            metaData['PhysicalSizeX'] = 1
            metaData['PhysicalSizeXOrigin'] = 0
            metaData['PhysicalSizeXUnit'] = ''
            metaData['PhysicalSizeY'] = 1
            metaData['PhysicalSizeYOrigin'] = 0
            metaData['PhysicalSizeYUnit'] = ''

        metaData['FileName'] = path

    return metaData


def ingest_NCEM_DM(paths):
    assert len(paths) == 1
    path = paths[0]

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = _metadata(path)
    start_doc.update(run_bundle.start_doc)
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    yield 'start', start_doc

    dm_handle = dm.fileDM(path, on_memory=True)
    num_t = _num_t(dm_handle)
    num_z = _num_z(dm_handle)
    first_frame = dm_handle.getSlice(0, 0, sliceZ2=0)['data']  # Most DM files have only 1 dataset
    shape = first_frame.shape
    dtype = first_frame.dtype

    delayed_get_slice = dask.delayed(get_slice)
    dask_data = da.stack([[da.from_delayed(delayed_get_slice(dm_handle, t, z), shape=shape, dtype=dtype)
                           for z in range(num_z)]
                          for t in range(num_t)])

    # Compose descriptor
    source = 'NCEM'
    frame_data_keys = {'raw': {'source': source,
                               'dtype': 'number',
                               'shape': (num_t, num_z, *shape)}}
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
    print(list(ingest_NCEM_DM(["/home/rp/data/NCEM/01_TimeSeriesImages_20images(1).dm3"])))
