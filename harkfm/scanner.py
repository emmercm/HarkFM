import json
import os.path
import re
import time

from PyQt5 import QtCore
from PyQt5.QtCore import QThread

import harkfm


class Scanner(object):
    _config = None

    storage = None

    def __init__(self):
        if self.__class__._config is None:
            # Parse JSON config
            json_file = os.path.splitext(__file__)[0] + '.json'
            self.__class__._config = harkfm.Util.json_load(json_file)
            # Compile JSON config
            if 'windows' in self.__class__._config:
                for window_id, window in enumerate(self.__class__._config['windows']):
                    for prop in window['window']:
                        self.__class__._config['windows'][window_id]['window'][prop] = re.compile(window['window'][prop])
                    for prop in window['regex']:
                        self.__class__._config['windows'][window_id]['regex'][prop] = re.compile(window['regex'][prop])
            if 'replace' in self.__class__._config:
                for category in self.__class__._config['replace']:
                    for replace_id, replace in enumerate(self.__class__._config['replace'][category]):
                        self.__class__._config['replace'][category][replace_id][0] = re.compile(
                            self.__class__._config['replace'][category][replace_id][0])

        if self.__class__.storage is None:
            self.__class__.storage = harkfm.Storage()

        class ScannerThread(QThread):
            updated = QtCore.pyqtSignal(dict)

            def setup(self, scanner):
                self.scanner = scanner

            def run(self):
                engine = harkfm.Engine()
                firefox = harkfm.Firefox()

                windows = []
                while True:
                    # Scan for a new window
                    while len(windows) == 0:
                        if 'windows' in self.scanner._config and len(self.scanner._config['windows']) > 0:
                            if os.name == 'nt':
                                import win32gui

                                def win_search(hwnd, win):
                                    # Possibility of window closing in the middle of this enum
                                    if not win32gui.IsWindow(hwnd):
                                        return
                                    # Get window properties
                                    w_class = win32gui.GetClassName(hwnd)
                                    w_text = win32gui.GetWindowText(hwnd)
                                    # Look for match in self.scanner._config['windows']
                                    for idx, window in enumerate(self.scanner._config['windows']):
                                        if (
                                            ('class' not in window['window'] or re.search(window['window']['class'], w_class)) and
                                            ('title' not in window['window'] or re.search(window['window']['title'], w_text))
                                        ):
                                            windows.append((idx, hwnd, w_class, win32gui.GetWindowText))
                                            break
                                win32gui.EnumWindows(win_search, windows)

                                if firefox.pid():
                                    hwnd = firefox.hwnd()
                                    hwnd = hwnd[0] if len(hwnd) > 0 else None
                                    w_class = win32gui.GetClassName(hwnd) if hwnd is not None else ''
                                    for tab in firefox.tabs():
                                        w_text = tab['title'] if 'title' in tab else ''
                                        for idx, window in enumerate(self.scanner._config['windows']):
                                            if (
                                                ('class' not in window['window'] or re.search(window['window']['class'], w_class)) and
                                                ('title' not in window['window'] or re.search(window['window']['title'], w_text))
                                            ):
                                                windows.append((idx, tab, w_class, firefox.tab_title))
                                                break

                        time.sleep(0.5)

                    # Get info from window
                    if len(windows) > 0:
                        if os.name == 'nt':
                            import win32gui

                            # Get window properties
                            window = self.scanner._config['windows'][windows[0][0]]
                            if type(windows[0][1]) is int and not win32gui.IsWindow(windows[0][1]):
                                windows = []
                                self.updated.emit({})
                                continue
                            w_class = windows[0][2](windows[0][1]) if hasattr(windows[0][2], '__call__') else windows[0][2]
                            w_text = windows[0][3](windows[0][1]) if hasattr(windows[0][3], '__call__') else windows[0][3]

                            # Check if we lost window match
                            if (
                                not w_text or
                                ('class' in window['window'] and not re.search(window['window']['class'], w_class)) or
                                ('title' in window['window'] and not re.search(window['window']['title'], w_text))
                            ):
                                windows = []
                                self.updated.emit({})
                                continue

                            # Parse window title (if changed)
                            if not hasattr(engine.current, 'w_text') or w_text != engine.current.w_text:
                                props = {'w_text': w_text, 'app': window['title']}
                                if 'icon' in window:
                                    props['app_icon'] = window['icon']
                                if 'title' in window['window']:
                                    w_text = harkfm.Util.regex(window['window']['title'], w_text)
                                for prop in window['regex']:
                                    props[prop] = harkfm.Util.regex(window['regex'][prop], w_text)
                                    # Do replacements
                                    if self.scanner.storage.config_get('settings/correct/scanner'):
                                        for replace in self.scanner._config['replace']['all']:
                                            props[prop] = re.sub(replace[0], replace[1], props[prop])
                                        for replace in self.scanner._config['replace'][prop]:
                                            props[prop] = re.sub(replace[0], replace[1], props[prop])

                                self.updated.emit(props)

                    time.sleep(0.1)

        def emit_updated(props):
            engine = harkfm.Engine()
            if props:
                engine.current = harkfm.Track(props)
            else:
                engine.current = None

        t = ScannerThread(harkfm.Interface.qMainWindow)
        t.updated.connect(emit_updated)
        t.setup(self)
        t.start()
