from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import QRect, QRectF
import pyqtgraph as pg
import numpy as np
from ncempy.io import dm
from pathlib import Path
from xicam.core.data import NonDBHeader

class FourDImageView(QWidget):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        
        #kwargs['dataSize'] = self.dataSize
        
        super(FourDImageView, self).__init__(*args, *kwargs)
        self.DPimageview = pg.ImageView()
        self.RSimageview = pg.ImageView()

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.DPimageview)
        self.layout().addWidget(self.RSimageview)
        
        self.DProi = pg.RectROI(pos=(0, 0), size=(10, 10), translateSnap=True, snapSize=1, scaleSnap=True)
        self.RSroi = pg.RectROI(pos=(0, 0), size=(2, 2), translateSnap=True, snapSize=1, scaleSnap=True)
        self.DProi.sigRegionChanged.connect(self.update)
        self.RSroi.sigRegionChanged.connect(self.update)

        DPview = self.DPimageview.view  # type: pg.ViewBox
        DPview.addItem(self.DProi)
        RSview = self.RSimageview.view  # type: pg.ViewBox
        RSview.addItem(self.RSroi)

    def setData(self, data):
        self.data = data
        
        self.DPlimit = QRectF(0,0,data.shape[2],data.shape[3])
        self.RSlimit = QRectF(0,0,data.shape[0],data.shape[1])
        self.DProi.maxBounds = self.DPlimit
        self.RSroi.maxBounds = self.RSlimit
        
        self.update()

    def update(self, *_, **__):
        self.DPimageview.setImage(np.sum(self.data[int(self.RSroi.pos().x()):
                                                   int(self.RSroi.pos().x() + self.RSroi.size().x()),
                                         int(self.RSroi.pos().y()):
                                         int(self.RSroi.pos().y() + self.RSroi.size().y()), :, :], axis=(1, 0)))
        self.RSimageview.setImage(np.log(np.sum(self.data[:, :,
                                         int(self.DProi.pos().x()):
                                         int(self.DProi.pos().x() + self.DProi.size().x()),
                                                int(self.DProi.pos().y()):
                                                int(self.DProi.pos().y() + self.DProi.size().y())], axis=(3, 2)) + 1))
