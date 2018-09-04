from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path
from ncempy.io import dm

class DMPlugin(DataHandlerPlugin):
    name = 'DMPlugin'

    DEFAULT_EXTENTIONS = ['.dm3', '.dm4']

    def __call__(self, path, *args, **kwargs):
        aa = dm.fileDM(path)
        aa.parseHeader()
        return aa.getDataset(kwargs.get('index', 0))['data']

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = dm.fileDM(path)
        md.parseHeader()
        return md.allTags

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})