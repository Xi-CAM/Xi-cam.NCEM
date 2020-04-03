from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.widgetplugin import QWidgetPlugin

from xicam.core import msg


class NCEMToolbar(QToolBar):
    name = 'NCEMToolbar'
    sigDeviceChanged = Signal(str)

    def __init__(self, headermodel: QStandardItemModel, selectionmodel: QItemSelectionModel):
        super(NCEMToolbar, self).__init__()

        self.headermodel = headermodel
        self.selectionmodel = selectionmodel
        self.headermodel.dataChanged.connect(self.updatedetectorcombobox)

        self.detectorcombobox = QComboBox()
        self.detectorcombobox.currentTextChanged.connect(self.sigDeviceChanged)

        self.addWidget(self.detectorcombobox)
        self.addSeparator()

    def updatedetectorcombobox(self, start, end):
        if self.headermodel.rowCount():
            devices = self.headermodel.item(self.selectionmodel.currentIndex().row()).header.devices()
            self.detectorcombobox.clear()
            self.detectorcombobox.addItems(devices)
