import time
import dask
import dask.array as da
from pathlib import Path

import event_model

import tifffile


def _get_slice(path, t):
    data = tifffile.imread(path, key=t)
    return data


def _num_t(path):
    """ Number of Tif pages
    """
    data = tifffile.TiffFile(path)
    num_t = len(data.pages)

    return num_t


def _metadata():
    metaData = {}

    # Store the X and Y pixel size, offset and unit
    metaData['PhysicalSizeX'] = 1
    metaData['PhysicalSizeXOrigin'] = 0
    metaData['PhysicalSizeXUnit'] = ''
    metaData['PhysicalSizeY'] = 1
    metaData['PhysicalSizeYOrigin'] = 0
    metaData['PhysicalSizeYUnit'] = ''

    return metaData


def ingest_NCEM_TIF(paths):
    assert len(paths) == 1
    path = paths[0]

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = metadata = _metadata()
    start_doc.update(run_bundle.start_doc)
    start_doc["sample_name"] = Path(paths[0]).resolve().stem
    yield 'start', start_doc

    num_t = _num_t(path)
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
    print(list(ingest_NCEM_TIF(
        ["/home/rp/data/Tender PFSA Beam Damage/N211_ARDry/Pilatus/N211ArDry_DamStudy_2460_20s_6402-00001.tif"])))
