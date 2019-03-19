import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.core.data import load_header, NonDBHeader

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
import pyqtgraph as pg
from functools import partial
from xicam.gui.widgets.dynimageview import DynImageView

from xicam.gui.widgets.metadataview import MetadataView
from . import widgets

from xicam.gui.widgets.tabview import TabView

from .patches import pyqtgraph_export
from .patches import pyqtgraph_tiffexporter


class NCEMPlugin(GUIPlugin):
    name = 'NCEM'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        # Data model
        self.headermodel = QStandardItemModel()

        # Selection model
        self.selectionmodel = QItemSelectionModel(self.headermodel)

        # Setup TabViews
        self.rawview = TabView(self.headermodel, self.selectionmodel, widgets.NCEMViewerPlugin, 'primary')

        self.fftview = TabView(self.headermodel, self.selectionmodel, widgets.FFTViewerPlugin, 'primary')

        self.fourDview = TabView(self.headermodel, self.selectionmodel, widgets.FourDImageView, 'primary')

        self.metadataview = MetadataView(self.headermodel, self.selectionmodel)

        self.toolbar = widgets.NCEMToolbar(self.headermodel, self.selectionmodel)

        self.stages = {
            'View': GUILayout(self.rawview, top=self.toolbar, right=self.metadataview),
            '4D STEM': GUILayout(self.fourDview, ),
            'FFT View': GUILayout(self.fftview, )
        }
        super(NCEMPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())
