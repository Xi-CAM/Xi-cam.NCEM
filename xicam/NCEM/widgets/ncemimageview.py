
import numpy as np

from xicam.gui.widgets.dynimageview import DynImageView


class NCEMImageView(DynImageView):
    def __init__(self, *args, **kwargs):
        super(NCEMImageView, self).__init__(*args, **kwargs)

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
        data = data[sl]
        return [(np.nanpercentile(np.where(data > np.nanmin(data), data, np.nanmax(data)), .1),
                np.nanpercentile(np.where(data < np.nanmax(data), data, np.nanmin(data)), 99.1))]