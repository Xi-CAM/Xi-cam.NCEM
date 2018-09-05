from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path
from ncempy.io import dm


# TODO: ask peter to add __enter__ and 'with' support to NCEMPY's dm module

class DMPlugin(DataHandlerPlugin):
    name = 'DMPlugin'

    DEFAULT_EXTENTIONS = ['.dm3', '.dm4']

    def __call__(self, path, index_z, index_t):
        aa = dm.fileDM(path)
        aa.parseHeader()
        return aa.getDataset(index_z)['data'][index_t]

    @classmethod
    def getEventDocs(cls, paths, descriptor_uid):
        for path in paths:
            for index_z in range(cls.num_z(path)):
                for index_t in range(cls.num_t(path)):
                    yield embedded_local_event_doc(descriptor_uid, 'primary', cls, (path, index_z, index_t))

    @staticmethod
    def num_z(path):
        f = dm.fileDM(path)
        f.parseHeader()
        return f.zSize[0]

    @staticmethod
    def num_t(path):
        f = dm.fileDM(path)
        f.parseHeader()
        return f.zSize[1]

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = dm.fileDM(path)
        md.parseHeader()
        return md.allTags

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})