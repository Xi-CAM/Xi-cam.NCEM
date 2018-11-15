from qtpy.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from ncempy.io import dm

class FourDImageView(QWidget):
    def __init__(self, *args, **kwargs):
        super(FourDImageView, self).__init__(*args, *kwargs)
        self.DPimageview = pg.ImageView()
        self.RSimageview = pg.ImageView()

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.DPimageview)
        self.layout().addWidget(self.RSimageview)

        self.DProi = pg.RectROI(pos=(0, 0), size=(2, 2), translateSnap=True, snapSize=1, scaleSnap=True)
        self.RSroi = pg.RectROI(pos=(0, 0), size=(2, 2), translateSnap=True, snapSize=1, scaleSnap=True)
        self.DProi.sigRegionChanged.connect(self.update)
        self.RSroi.sigRegionChanged.connect(self.update)

        DPview = self.DPimageview.view  # type: pg.ViewBox
        DPview.addItem(self.DProi)
        RSview = self.RSimageview.view  # type: pg.ViewBox
        RSview.addItem(self.RSroi)

        # self.x = 0
        # self.y = 0
        # self.kx = 0
        # self.ky = 0

    def setData(self, data):
        self.data = data
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
                                         int(self.DProi.pos().y() + self.DProi.size().y())], axis=(3, 2))+1))


if __name__ == '__main__':
    qapp = QApplication([])

    fdview = FourDImageView()
    fdview.show()
    
    data = dm.dmReader(r'C:\Users\Peter\Data\Te NP 4D-STEM\07_45x8 ss=5nm_spot11_CL=100 0p1s_alpha=4p63mrad_bin=4_300kV.dm4')['data']
    data = data.reshape((10,50,512,512))
    
    #data = np.fromfunction(lambda x, y, kx, ky: (x - kx) ** 2 + (y - ky) ** 2, (20, 20, 512, 512))
    fdview.setData(data)

    qapp.exec_()
