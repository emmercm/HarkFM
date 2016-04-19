import copy
import json
import os.path
import sys

import harkfm


class Storage(object):
    config = None
    config_file = None

    def __init__(self):
        if self.__class__.config is None:
            self.__class__.config_file = os.path.dirname(sys.argv[0]) + 'storage.json'
            self.__class__.config = harkfm.Util.json_load(self.__class__.config_file)

    # Get a value out of the config
    def config_get(self, path, default=None):
        path = path.split('/')
        item = self.__class__.config
        for key in path:
            if key in item:
                item = item[key]
            else:
                return default
        return copy.copy(item)

    # Set a value in the config (and write to disk)
    def config_set(self, path, value):
        path = path.split('/')
        item = self.__class__.config
        for key in path[:-1]:
            if key not in item:
                item[key] = {}
            item = item[key]
        if path[-1] not in item or item[path[-1]] != value:
            if value is None and path[-1] in item:
                del item[path[-1]]
            else:
                item[path[-1]] = value
            with open(self.__class__.config_file, 'w') as json_content:
                json.dump(self.__class__.config, json_content)

    def config_append(self, path, value):
        item = self.config_get(path)
        if item is None:
            item = []
        if type(item) is list:
            item.append(value)
            self.config_set(path, item)
