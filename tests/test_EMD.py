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