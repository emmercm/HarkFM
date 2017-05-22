import glob
import json
import logging
import os

import psutil

class Firefox(object):
    _filename = None
    _modified = None
    _session = {}
    _session_lock = False

    _pids_all = []
    _pids_firefox = []

    logger = None

    def __init__(self):
        if self.__class__.logger is None:
            self.__class__.logger = logging.getLogger('root')

    @property
    def filename(self):
        # Forget any invalid sessionstore file
        if self.__class__._filename is not None and not os.path.exists(self.__class__._filename):
            self.__class__._filename = None

        # Find sessionstore file
        try:
            if self.__class__._filename is None:
                profiles = None
                if os.name == 'nt':
                    profiles = os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles'
                if profiles is not None:
                    sessions = glob.glob(os.environ['APPDATA'] + '\\Mozilla\\Firefox\\Profiles\\*\\sessionstore-backups\\recovery.js')
                    if len(sessions) > 0:
                        self.__class__._filename = sorted(sessions, key=lambda session: os.path.getmtime(session), reverse=True)[0]
        except Exception as e:
            self.__class__.logger.warn('%s  %s', type(e), e)
            self.__class__._filename = None

        return self.__class__._filename

    @property
    def session(self):
        if not self._session_lock:
            # Read sessionstore file (if changed)
            try:
                if self.filename is not None and os.path.getmtime(self.filename) != self.__class__._modified:
                    with open(self.filename, 'r', encoding='utf-8') as content:
                        self.__class__._session = json.loads(content.read())
                    self.__class__._modified = os.path.getmtime(self.filename)
            except Exception as e:
                self.__class__.logger.warn('%s  %s', type(e), e)
                self.__class__._modified = None
                self.__class__._session = {}

        return self.__class__._session

    def pids(self):
        # If running processes hasn't changed return the Firefox PID cache
        pids_all = psutil.pids()
        if pids_all == self.__class__._pids_all:
            return self.__class__._pids_firefox
        self.__class__._pids_all = pids_all

        # Build and return Firefox PID cache
        pids_firefox = []
        for p in psutil.process_iter():
            try:
                if os.path.splitext(p.name())[0] == 'firefox':
                    pids_firefox.append(p.pid)
            except psutil.NoSuchProcess:
                pass
        self.__class__._pids_firefox = pids_firefox
        return self.__class__._pids_firefox

    def hwnd(self, pid=None):
        if pid is None:
            pid = self.pids()
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
        tabs = []
        if 'windows' in self.session:
            self._session_lock = True
            for window in self.session['windows'][::-1]:
                if 'tabs' in window:
                    for tab in window['tabs'][::-1]:
                        if 'entries' in tab and 'index' in tab and len(tab['entries']) >= tab['index']:
                            entry = tab['entries'][tab['index']-1]
                            tabs.append(entry)
            self._session_lock = False
        return tabs

    def tab_title(self, docshellID):
        if type(docshellID) is dict and 'docshellID' in docshellID:
            docshellID = docshellID['docshellID']
        for tab in self.tabs():
            if 'docshellID' in tab and tab['docshellID'] == docshellID:
                return tab['title'] if 'title' in tab else ''
        return ''