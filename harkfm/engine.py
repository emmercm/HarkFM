import logging
import os.path
import time

import jsonpickle
import pylast

import harkfm


class Engine(object):
    _current = None
    _lfm_network = None
    _tts = None

    _thread_scrobbler_log = None
    _thread_scrobbler = None

    config = None
    correct_thread = None

    storage = None
    logger = None

    def __init__(self):
        if self.__class__.config is None:
            # Parse JSON config
            json_file = os.path.splitext(__file__)[0] + '.json'
            self.__class__.config = harkfm.Util.json_load(json_file)

        if self.__class__.storage is None:
            self.__class__.storage = harkfm.Storage()
        if self.__class__.logger is None:
            self.__class__.logger = logging.getLogger('root')

        self.lfm_login()
        self.scrobbler_log()

    @property
    def current(self):
        return self.__class__._current

    @current.setter
    def current(self, value):
        if value != self.__class__._current:
            old = self.__class__._current

            self.__class__._current = value
            if self.__class__._current is not None:
                self.__class__._current.start = int(time.time())
                self.__class__._current.correct()

            if self.__class__._lfm_network is not None:
                # Song has changed
                if value != old:
                    self.tts()
                    self.scrobble()
                # Re-render index if visible
                interface = harkfm.Interface()
                interface.index()

    @property
    def scrobbling(self):
        if self.__class__._thread_scrobbler is not None:
            return self.__class__._thread_scrobbler.isRunning()
        return False

    def scrobbler_log(self):
        def scrobbler_log_do(upd):
            while True:
                if (
                    self.current is not None
                    and self.__class__._lfm_network is not None
                    and self.__class__.storage.config_get('settings/scrobble/enabled')
                ):
                    elapsed_percent = (time.time() - self.current.start) / self.current.track_duration * 100
                    # Listen
                    if (
                        self.current
                        and not self.current.listened
                        and elapsed_percent >= float(self.__class__.storage.config_get('settings/scrobble/listen_percent'))
                    ):
                        self.current.listen()
                    # Queue scrobble
                    if (
                        self.current
                        and not self.current.queued
                        and elapsed_percent >= float(self.__class__.storage.config_get('settings/scrobble/scrobble_percent'))
                    ):
                        self.__class__.storage.config_append('queue', jsonpickle.encode(self.current))
                        self.current.queued = int(time.time())
                time.sleep(0.5)
        if self.__class__._thread_scrobbler_log is None:
            self.__class__._thread_scrobbler_log = harkfm.Util.thread(scrobbler_log_do, None, None)

    def scrobble(self):
        def scrobble_do(upd):
            harkfm.Track()  # init static classes
            queue = self.__class__.storage.config_get('queue')
            if type(queue) is list and len(queue) > 0:
                while queue:
                    # Consume and scrobble
                    item = queue.pop()
                    track = jsonpickle.decode(item)
                    if not track.scrobble():
                        queue.insert(0, item)
                        break
                self.__class__.storage.config_set('queue', queue)
        if (
            self.__class__._lfm_network is not None
            and self.__class__._thread_scrobbler is None or not self.__class__._thread_scrobbler.isRunning()
        ):
            self.__class__._thread_scrobbler = harkfm.Util.thread(scrobble_do, None, None)

    def lfm_login(self):
        if self.__class__._lfm_network is None:
            username = self.__class__.storage.config_get('apis/last.fm/username')
            session_key = self.__class__.storage.config_get('apis/last.fm/session_key')
            if session_key is not None:
                api_key = harkfm.Engine.config['apis']['last.fm']['key']
                api_secret = harkfm.Engine.config['apis']['last.fm']['secret']
                try:
                    self.__class__._lfm_network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret,
                                                                       username=username, session_key=session_key)
                    self.__class__._lfm_network.enable_caching()
                    if self.current is not None:
                        self.current.correct()
                except Exception as e:
                    self.__class__.logger.warn('%s  %s  "%s"', type(e), e, username)

        if self.__class__._lfm_network is not None and self.__class__._lfm_network.username is None:
            try:
                user = self.__class__._lfm_network.get_authenticated_user()
                if user is not None:
                    self.__class__._lfm_network.username = user.get_name()
                    self.__class__.storage.config_set('apis/last.fm/username', self.__class__._lfm_network.username)
            except Exception as e:
                self.__class__.logger.warn('%s  %s', type(e), e)

        return self.__class__._lfm_network

    def lfm_logout(self):
        self.__class__.storage.config_set('apis/last.fm/username', None)
        self.__class__.storage.config_set('apis/last.fm/session_key', None)
        self.__class__._lfm_network = None
        self.current = None
        interface = harkfm.Interface()
        interface.login()

    def lfm_props(self):
        if self.__class__._lfm_network is None:
            return {}
        else:
            return self.__class__._lfm_network.__dict__

    def tts(self):
        if (
            self.current
            and self.current.track
            and self.current.artist
            and self.__class__.storage.config_get('settings/tts/enabled')
        ):
            speech = self.current.track + ' by ' + self.current.artist
            if os.name == 'nt':
                if self.__class__._tts is None:
                    import win32com.client
                    self.__class__._tts = win32com.client.Dispatch('SAPI.SpVoice')
                    self.__class__._tts.Rate = -2
                try:
                    self.__class__._tts.Speak(speech, 3)  # SVSFlagsAsync + SVSFPurgeBeforeSpeak
                except:
                    pass
