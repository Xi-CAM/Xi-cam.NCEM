import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *

from databroker.core import BlueskyRun

from xicam.core.data import NonDBHeader

from xicam.plugins import GUIPlugin, GUILayout
from . import widgets

from xicam.gui.widgets.tabview import TabView

from .patches import pyqtgraph_export
from .patches import pyqtgraph_tiffexporter
from . import ingestors  # necessary unused import; registers mimetypes

from xicam.NCEM.ingestors import DMPlugin


class NCEMPlugin(GUIPlugin):
    name = 'NCEM'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        # Data model
        self.catalogModel = QStandardItemModel()

        # Selection model
        self.selectionmodel = QItemSelectionModel(self.catalogModel)

        # Setup TabViews
        self.rawview = TabView(self.catalogModel, self.selectionmodel, widgets.NCEMViewerPlugin, 'primary', field='raw')

        # self.fftview = TabView(self.catalogModel, self.selectionmodel, widgets.FFTViewerPlugin, 'primary')

        #self.fourDview = TabView(self.headermodel, self.selectionmodel, widgets.FourDImageView, 'primary')

        # self.metadataview = MetadataView(self.catalogModel, self.selectionmodel, excludedkeys=('uid','descriptor','data'))

        # self.toolbar = widgets.NCEMToolbar(self.catalogModel, self.selectionmodel)

        self.stages = {
            'View': GUILayout(self.rawview, )  # top=self.toolbar, )#right=self.metadataview),
            # 'View': GUILayout(self.rawview, top=self.toolbar),
            # '4D STEM': GUILayout(self.fourDview, ),
            # 'FFT View': GUILayout(self.fftview, )
        }
        super(NCEMPlugin, self).__init__()

    def appendCatalog(self, catalog: BlueskyRun, *args, **kwargs):

        displayName = ""
        if 'sample_name' in catalog.metadata['start']:
            displayName = catalog.metadata['start']['sample_name']
        elif 'scan_id' in catalog.metadata['start']:
            displayName = f"Scan: {catalog.metadata['start']['scan_id']}"
        else:
            displayName = f"UID: {catalog.metadata['start']['uid']}"

        item = QStandardItem()
        item.setData(displayName, Qt.DisplayRole)
        item.setData(catalog, Qt.UserRole)
        self.catalogModel.appendRow(item)
        self.catalogModel.dataChanged.emit(item.index(), item.index())

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())
