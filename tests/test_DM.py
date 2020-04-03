import pytest
from xicam.NCEM.ingestors.DMPlugin import ingest_NCEM_DM


# TODO: add fixture that writes temp data file with ncempy for tests

@pytest.fixture
def DM_path():
    return "/home/rp/data/NCEM/01_TimeSeriesImages_20images(1).dm3"


def test_slicing(DM_path):
    docs = list(ingest_NCEM_DM([DM_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (20, 1, 1024, 1024)
    assert data[1, 0].compute().shape == (1024, 1024)
