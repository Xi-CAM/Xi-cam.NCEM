import pytest
from ncempy.io import ser
from xicam.NCEM.ingestors.SERPlugin import ingest_NCEM_SER, _get_slice


# TODO: add fixture that writes temp data file with ncempy for tests

@pytest.fixture
def SER_path():
    return "/home/rp/data/NCEM/10_series_1.ser"


def test_slicing(SER_path):
    # with ser.fileSER(SER_path) as ser_obj:
    assert _get_slice(SER_path, 0).shape == (512, 512)
    docs = list(ingest_NCEM_SER([SER_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (29, 512, 512)
    assert data[0].compute().shape == (512, 512)
