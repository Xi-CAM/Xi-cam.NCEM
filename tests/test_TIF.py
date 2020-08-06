import pytest

from pathlib import Path
import tempfile

import numpy as np
import tifffile

from xicam.NCEM.ingestors.TIFPlugin import ingest_NCEM_TIF


# TODO: move file creation to fixture

@pytest.fixture
def TIF_path():
    return "/home/rp/data/Tender PFSA Beam Damage/3M825_ARDry/Pilatus/3M825_ARDry_2460_10sTest2_ESZ165_6243-00001.tif"


def test_slicing():

    # Write a small TIF file
    # The resolution is written in imageJ format for a volume with voxel size 0.1 x 0.2 x 0.3
    # See tifffile notes on pypi project description
    dd, _, _ = np.mgrid[0:30, 0:40, 0:50]
    dd = dd.astype('<u2')
    tmp = tempfile.TemporaryDirectory()
    fPath = str(Path(tmp.name) / Path('temp_tif.tif'))
    tifffile.imsave(fPath, dd, imagej=True, resolution=(1/0.2, 1/0.3), metadata={'spacing': '0.1', 'unit': 'um'})

    docs = list(ingest_NCEM_TIF([fPath]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (30, 40, 50)
    assert data[0].compute().shape == (40, 50)
