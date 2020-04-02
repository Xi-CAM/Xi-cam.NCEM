import pytest
from xicam.NCEM.ingestors.TIFPlugin import ingest_NCEM_TIF


# TODO: add fixture that writes temp data file with ncempy for tests

@pytest.fixture
def TIF_path():
    return "/home/rp/data/Tender PFSA Beam Damage/3M825_ARDry/Pilatus/3M825_ARDry_2460_10sTest2_ESZ165_6243-00001.tif"


def test_slicing(TIF_path):
    docs = list(ingest_NCEM_TIF([TIF_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (1, 619, 487)
    assert data[0].compute().shape == (619, 487)
