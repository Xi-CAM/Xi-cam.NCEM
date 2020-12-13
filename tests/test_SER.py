from pathlib import Path

import pytest
from xicam.NCEM.ingestors.SERPlugin import ingest_NCEM_SER, _get_slice


@pytest.fixture
def SER_path():
    """SER files cant be written. We can only use data from a microscope"""
    dPath = Path.home()
    return str(dPath / Path('data') / Path('10_series_1.ser'))


def test_slicing(SER_path):
    assert _get_slice(SER_path, 0).shape == (512, 512)
    docs = list(ingest_NCEM_SER([SER_path]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (29, 512, 512)
    assert data[0].compute().shape == (512, 512)
