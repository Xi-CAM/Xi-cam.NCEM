import pytest

from pathlib import Path
import tempfile

import numpy as np
from ncempy.io import mrc
from xicam.NCEM.ingestors.MRCPlugin import ingest_NCEM_MRC


# TODO: move file creation to fixture

@pytest.fixture
def mrc_path():
    """Write a small MRC file to a temporary directory and file location.

    THIS DOES NOT WORK. NOT SURE WHY. -PAE

    Returns
    -------
        : string
            The path to the temporary file.
    """
    dd, _, _ = np.mgrid[0:30, 0:40, 0:50]
    dd = dd.astype('<u2')

    tmp = tempfile.TemporaryDirectory()
    fPath = Path(tmp.name) / Path('temp_mrc.mrc')

    mrc.mrcWriter(str(fPath), dd, (0.1, 0.2, 0.3))

    return str(fPath)


def test_ingest():

    # Write a small mrc file
    dd, _, _ = np.mgrid[0:30, 0:40, 0:50]
    dd = dd.astype('<u2')
    tmp = tempfile.TemporaryDirectory()
    fPath = str(Path(tmp.name) / Path('temp_mrc.mrc'))
    mrc.mrcWriter(fPath, dd, (0.1, 0.2, 0.3))

    # Test
    with mrc.fileMRC(fPath) as mrc_obj:
        assert mrc_obj.getSlice(0).shape == (40, 50)
    docs = list(ingest_NCEM_MRC([fPath]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (30, 40, 50)
    assert data[0].compute().shape == (40, 50)
