import glob
import json
import os

import psutil

class Firefox(object):
    _filename = None
    _modified = None
    _session = {}

    def __init__(self):
        self.__sessionstore()

    def __sessionstore(self):
        # Reset variables if Firefox not running
        if not self.pid():
            self.__class__._filename = None
            self.__class__._modified = None
            self.__class__._session = {}

        # Forget any invalid sessionstore file
        if self.__class__._filename is not None and not os.path.exists(self.__class__._filename):
            self.__class__._filename = None

        # Find sessionstore file
        if self.__class__._filename is None:
            profiles = None
            if os.name == 'nt':
                profiles = os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles'
            if profiles is not None:
                sessions = glob.glob(os.environ['APPDATA'] + '\\Mozilla\\Firefox\\Profiles\\*\\sessionstore-backups\\recovery.js')
                if len(sessions) > 0:
                    self.__class__._filename = sorted(sessions, key=lambda session: os.path.getmtime(session), reverse=True)[0]

        # Read sessionstore file (if changed)
        if self.__class__._filename is not None and os.path.getmtime(self.__class__._filename) != self.__class__._modified:
            with open(self.__class__._filename, 'r', encoding='utf-8') as content:
                self.__class__._session = json.loads(content.read())
            self.__class__._modified = os.path.getmtime(self.__class__._filename)

    def pid(self):
        pids = []
        for p in psutil.process_iter():
            try:
                if os.path.splitext(p.name())[0] == 'firefox':
                    pids.append(p.pid)
            except psutil.NoSuchProcess:
                pass
        return pids

    def hwnd(self, pid=None):
        if pid is None:
            pid = self.pid()
        if type(pid) is not list:
            pid = [pid]

        windows = []

        if os.name == 'nt':
            import win32gui, win32process
            def win_search(hwnd, win):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    if win32process.GetWindowThreadProcessId(hwnd)[1] in pid:
                        win.append(hwnd)
            win32gui.EnumWindows(win_search, windows)

        return windows

    def tabs(self):
        self.__sessionstore()
        tabs = []
        if 'windows' in self.__class__._session:
            for window in self.__class__._session['windows'][::-1]:
                if 'tabs' in window:
                    for tab in window['tabs'][::-1]:
                        if 'entries' in tab and 'index' in tab and len(tab['entries']) >= tab['index']:
                            entry = tab['entries'][tab['index']-1]
                            tabs.append(entry)
        return tabs

    def tab_title(self, docshellID):
        if type(docshellID) is dict and 'docshellID' in docshellID:
            docshellID = docshellID['docshellID']
        for tab in self.tabs():
            if tab['docshellID'] == docshellID:
                return tab['title'] if 'title' in tab else ''
        return ''