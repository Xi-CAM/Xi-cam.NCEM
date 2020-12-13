import pytest

from pathlib import Path
import tempfile

import numpy as np
from ncempy.io import mrc
from xicam.NCEM.ingestors.MRCPlugin import ingest_NCEM_MRC


@pytest.fixture
def temp_file():
    tt = tempfile.NamedTemporaryFile(mode='wb')
    tt.close() # need to close the file to use it later
    return Path(tt.name)


def test_ingest(temp_file):
    # Write out a temporary mrc file
    mrc.mrcWriter(temp_file, np.ones((10, 11, 12), dtype=np.float32), (1, 2, 3))

    assert temp_file.exists() is True

    # Test
    with mrc.fileMRC(temp_file) as mrc_obj:
        assert mrc_obj.getSlice(0).shape == (11, 12)
    docs = list(ingest_NCEM_MRC([temp_file]))
    event_doc = docs[2][1]
    data = event_doc['data']['raw']
    assert data.shape == (10, 11, 12)
    assert data[0].compute().shape == (11, 12)
