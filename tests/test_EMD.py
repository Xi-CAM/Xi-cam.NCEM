from pathlib import Path
import tempfile

import pytest

import numpy as np

from ncempy.io import emd
from xicam.NCEM.ingestors.EMDPlugin import ingest_NCEM_EMD, _get_slice
from databroker.in_memory import BlueskyInMemoryCatalog


@pytest.fixture
def temp_file():
    tt = tempfile.NamedTemporaryFile(mode='wb')
    tt.close()  # need to close the file to use it later
    return Path(tt.name)


@pytest.fixture
def EMD_multi_path():
    """Write a small Berkeley EMD file with 2 data sets to a tempfile

    """
    dd, _, _ = np.mgrid[0:30, 0:40, 0:50]
    dd = dd.astype('<u2')

    dd2, _, _ = np.mgrid[0:60, 0:80, 0:100]
    dd2 = dd2.astype('<u2')

    tmp = tempfile.NamedTemporaryFile(mode='wb')
    tmp.close()  # need to close the file to use it later
    fPath = str(Path(tmp.name))
    with emd.fileEMD(fPath, readonly=False) as f0:
        dims = emd.defaultDims(dd)
        f0.put_emdgroup('test1', dd, dims)

        dims2 = emd.defaultDims(dd2)
        f0.put_emdgroup('test2', dd2, dims2)
    return fPath


def test_slicing(temp_file):
    dd = np.ones((10, 11, 12), dtype=np.uint16)
    with emd.fileEMD(temp_file, readonly=False) as emd0:
        dims = emd.defaultDims(dd)
        emd0.put_emdgroup('test', dd, dims)
    with emd.fileEMD(temp_file) as emd_obj:
        assert _get_slice(emd_obj, 0).shape == (11, 12)
    docs = list(ingest_NCEM_EMD([str(temp_file)]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (10, 11, 12)
    assert data[0].compute().shape == (11, 12)


def test_ingest_emd_berkeley(temp_file):
    dd = np.ones((10, 11, 12), dtype=np.uint16)
    with emd.fileEMD(temp_file, readonly=False) as emd0:
        dims = emd.defaultDims(dd)
        emd0.put_emdgroup('test', dd, dims)

    # Test slicing
    with emd.fileEMD(temp_file) as emd_obj:
        dd0 = emd_obj.list_emds[0]['data']
        assert dd0[0, :, :].shape == (11, 12)

    # Test ingest
    docs = list(ingest_NCEM_EMD([str(temp_file)]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (10, 11, 12)
    assert data[0].compute().shape == (11, 12)


def test_multi_device(temp_file):
    dd = np.ones((10, 11, 12), dtype=np.uint16)
    with emd.fileEMD(temp_file, readonly=False) as emd0:
        dims = emd.defaultDims(dd)
        emd0.put_emdgroup('test', dd, dims)
        # Change shape and write again to simulate a second data set
        dd2 = dd.reshape(5, 22, 12)
        dims2 = emd.defaultDims(dd2)
        emd0.put_emdgroup('test2', dd2, dims2)
    del dd, dd2, dims, dims2

    # Ingest and get the first data set.
    docs = list(ingest_NCEM_EMD([str(temp_file)]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (10, 11, 12)
    assert data[0].compute().shape == (11, 12)

    event_doc = docs[4][1]
    data = event_doc['data']['raw']
    assert data.shape == (5, 22, 12)
    assert data[0].compute().shape == (22, 12)

    catalog = BlueskyInMemoryCatalog()
    start = docs[0][1]
    stop = docs[-1][1]
    others = docs[1:-2]

    def doc_gen():
        yield from docs

    catalog.upsert(start, stop, doc_gen, [], {})

    run_catalog = catalog[-1]
    stream_names = list(run_catalog)
    print(stream_names)
    run_catalog[stream_names[0]].to_dask()['raw'].compute()
    run_catalog[stream_names[1]].to_dask()['raw'].compute()
