import pytest

import tempfile
from pathlib import Path
import numpy as np
from ncempy.io import emd
from xicam.NCEM.ingestors.EMDPlugin import ingest_NCEM_EMD, _get_slice


# TODO: move file creation to fixture

@pytest.fixture
def EMD_path():
    return "/home/rp/data/NCEM/Acquisition_18.emd"


def test_ingest_emd_berkeley():

    # Write a small Berkeley EMD file
    dd, _, _ = np.mgrid[0:30, 0:40, 0:50]
    dd = dd.astype('<u2')
    tmp = tempfile.TemporaryDirectory()
    fPath = str(Path(tmp.name) / Path('temp_emd_berkeley.emd'))
    with emd.fileEMD(fPath, readonly=False) as f0:
        dims = emd.defaultDims(dd)
        f0.put_emdgroup('test', dd, dims)

    # Test slicing
    with emd.fileEMD(fPath, readonly=True) as emd_obj:
        dd0 = emd_obj.list_emds[0]['data']
        assert dd0[0, :, :].shape == (40, 50)

    # Test ingest
    docs = list(ingest_NCEM_EMD([fPath]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (30, 40, 50)
    assert data[0].compute().shape == (40, 50)
