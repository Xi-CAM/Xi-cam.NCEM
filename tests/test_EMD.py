import pytest
from ncempy.io import emd
from xicam.NCEM.ingestors.EMDPlugin import ingest_NCEM_EMD, _get_slice


# TODO: add fixture that writes temp data file with ncempy for tests

@pytest.fixture
def EMD_path():
    return "/home/rp/data/NCEM/Acquisition_18.emd"


def test_slicing(EMD_path):
    with emd.fileEMD(EMD_path) as emd_obj:
        assert _get_slice(emd_obj, 0).shape == (1024, 1024)
    docs = list(ingest_NCEM_EMD([EMD_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (1, 1024, 1024)
    assert data[0].compute().shape == (1024, 1024)


@pytest.fixture
def EMD_multi_path():
    return "C:\\Users\\LBL\\PycharmProjects\\merged-repo\\Xi-cam.NCEM\\tests\\twoDatasets.emd"


def test_multi_device(EMD_multi_path):
    docs = list(ingest_NCEM_EMD([EMD_multi_path]))
    print(docs)
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (1, 512, 512)
    assert data[0].compute().shape == (512, 512)

    event_doc = docs[4][1]
    data = event_doc['data']['raw']
    assert data.shape == (2, 1024, 1024)
    assert data[0].compute().shape == (1024, 1024)

    from databroker.in_memory import BlueskyInMemoryCatalog

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