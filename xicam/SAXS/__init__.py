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

from xicam.gui.widgets.tabview import TabView


class NCEMPlugin(GUIPlugin):
    name = 'NCEM'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        # Data model
        self.headermodel = QStandardItemModel()

        # Setup TabViews
        self.rawview = TabView(self.headermodel,
                               pluginmanager.getPluginByName('NCEMViewerPlugin',
                                                             'WidgetPlugin').plugin_object,
                                          'primary')

        self.stages = {
            'View': GUILayout(self.rawview,),
        }
        super(NCEMPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())

