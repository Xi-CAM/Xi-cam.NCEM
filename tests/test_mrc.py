import pytest
from ncempy.io import mrc
from xicam.NCEM.ingestors.MRCPlugin import ingest_NCEM_MRC, _get_slice


# TODO: add fixture that writes temp data file with ncempy for tests

@pytest.fixture
def MRC_path():
    return "/home/rp/data/NCEM/Te_80k_L100mm_80Kx(1).mrc"


def test_slicing(MRC_path):
    # with mrc.fileMRC(MRC_path) as mrc_obj:
    assert _get_slice(MRC_path, 0).shape == (1024, 1024)
    docs = list(ingest_NCEM_MRC([MRC_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (151, 1024, 1024)
    assert data[0].compute().shape == (1024, 1024)
