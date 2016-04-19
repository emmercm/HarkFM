class Util(object):
    @staticmethod
    def json_load(file):
        import json
        import logging
        import re
        try:
            with open(file, 'r', encoding='utf-8') as content:
                content = content.read()
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                content = re.sub(r'([^:])//.*?$', r'\1', content, flags=re.MULTILINE)
                return json.loads(content)
        except Exception as e:
            logger = logging.getLogger('root')
            logger.warn('%s  %s', type(e), e)
        return {}

    @staticmethod
    def thread(do, upd, end):
        from PyQt5 import QtCore
        from PyQt5.QtCore import QThread
        import harkfm

        class UtilThread(QThread):
            updated = QtCore.pyqtSignal()
            end = QtCore.pyqtSignal()

            def setup(self, do, upd):
                self.do = do
                self.upd = upd

            def run(self):
                self.do(self.updated)
                self.end.emit()

        thread = UtilThread(harkfm.Interface.qMainWindow)
        if upd is not None:
            thread.updated.connect(upd)
        if end is not None:
            thread.end.connect(end)
        thread.setup(do, upd)
        thread.start()
        return thread

    @staticmethod
    def regex(pattern, string):
        import re
        regex = re.search(pattern, string)
        if regex is not None:
            groups = regex.groups()
            if len(groups) > 0:
                string = groups[0]
            return string
