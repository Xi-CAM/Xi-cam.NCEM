import functools
import numpy as np

from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import CatalogView

class NCEMImageView(DynImageView):
    def __init__(self, *args, **kwargs):
        super(NCEMImageView, self).__init__(*args, **kwargs)

    @functools.lru_cache(maxsize=10, typed=False)
    def quickMinMax(self, data):
        """
        Estimate the min/max values of *data* by subsampling.
        Removes 0.1% on the top and bottom for TEM data.
        """
        if data is None:
            return 0, 0
        ax = np.argmax(data.shape)
        sl = [slice(None)] * data.ndim
        sl[ax] = slice(None, None, max(1, int(data.size // 1e6)))
        data = data[tuple(sl)]
        return [(np.nanpercentile(np.where(data > np.nanmin(data), data, np.nanmax(data)), .1),
                np.nanpercentile(np.where(data < np.nanmax(data), data, np.nanmin(data)), 99.9))]


class NCEMFFTView(DynImageView):
    def __init__(self, *args, **kwargs):
        super(NCEMFFTView, self).__init__(*args, **kwargs)

    def quickMinMax(self, data):
        """
        Estimate the min/max values of *data* by subsampling.
        Removes 0.1% on the top and bottom for TEM data.
        """
        if data is None:
            return 0, 0
        ax = np.argmax(data.shape)
        sl = [slice(None)] * data.ndim
        sl[ax] = slice(None, None, max(1, int(data.size // 1e6)))
        data = data[tuple(sl)]
        return [(np.nanpercentile(np.where(data > np.nanmin(data), data, np.nanmax(data)), .1),
                np.nanpercentile(np.where(data < np.nanmax(data), data, np.nanmin(data)), 99.9))]


class NCEMCatalogView(CatalogView):
    def __init__(self, *args, **kwargs):
        super(NCEMCatalogView, self).__init__(*args, **kwargs)

    def quickMinMax(self, data):
        """
        Estimate the min/max values of *data* by subsampling. MODIFIED TO USE THE 99.9TH PERCENTILE instead of max.
        """
        if data is None:
            return 0, 0

        sl = slice(None, None, max(1, int(data.size // 1e6)))
        data = np.asarray(data[sl])
        data0 = data[0:200, :, :]
        levels = [np.nanmin(data0),
                  np.nanpercentile(np.where(data0 < np.nanmax(data0), data0, np.nanmin(data0)), 99.9)]

        return [levels]
