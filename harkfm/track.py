import logging
import time

import lib.pygn as pygn
import pylast

import harkfm


class Track(object):
    storage = None
    engine = None
    interface = None
    logger = None

    def __init__(self, props=None):
        if props is None:
            props = {}
        if self.__class__.storage is None:
            self.__class__.storage = harkfm.Storage()
        if self.__class__.engine is None:
            self.__class__.engine = harkfm.Engine()
        if self.__class__.interface is None:
            self.__class__.interface = harkfm.Interface()
        if self.__class__.logger is None:
            self.__class__.logger = logging.getLogger('root')

        self.app = None
        self.app_icon = None

        self._artist = None
        self._artist_corrected = None
        self.artist_img = None
        self.artist_url = None
        self.artist_wiki = None
        self.artist_listeners = 0
        self.artist_plays_global = 0
        self.artist_plays = 0
        self.artist_tags = []
        self.artist_similar = []

        self._track = None
        self._track_corrected = None
        self.track_url = None
        self.track_wiki = None
        self.track_duration = 3 * 60  # default tracks to 3 minutes
        self.track_plays = 0
        self.track_tags = []
        self.track_loved = None

        self._album = None
        self._album_corrected = None
        self.album_img = None
        self.album_url = None
        self.album_wiki = None
        self.album_year = 0

        self.mood = []
        self.genre = []
        self.tempo = 0

        self.start = 0
        self.listened = 0
        self.queued = 0

        self._corrected_gn = False
        self._corrected_lfm = False

        for prop in props.keys():
            setattr(self, prop, props[prop])

    @property
    def artist(self):
        return self._artist_corrected or self._artist

    @artist.setter
    def artist(self, value):
        self._artist = value

    @property
    def track(self):
        return self._track_corrected or self._track

    @track.setter
    def track(self, value):
        self._track = value

    @property
    def album(self):
        return self._album_corrected or self._album

    @album.setter
    def album(self, value):
        self._album = value

    def correct(self):
        self.__correct_gn()

    def __correct_gn(self):
        def gn_do(upd):
            pygn_client = self.__class__.engine.config['apis']['gracenote']['client_id']
            if pygn_client:
                pygn_user = self.__class__.storage.config_get('apis/gracenote/user_id')
                if pygn_user is None:
                    pygn_user = pygn.register(self.__class__.engine.config['apis']['gracenote']['client_id'])
                    self.__class__.storage.config_set('apis/gracenote/user_id', pygn_user)
                try:
                    grace = pygn.search(clientID=pygn_client, userID=pygn_user,
                                        artist=self.artist, track=self.track, album=self.album)
                    if type(grace) is pygn.gnmetadata:
                        self.artist_img = grace['artist_image_url']
                        self.artist_url = grace['artist_bio_url']
                        self._album_corrected = grace['album_title']
                        self.album_img = grace['album_art_url']
                        if grace['album_year'] and int(grace['album_year']) > 1900:
                            self.album_year = grace['album_year']
                        self.mood = [grace['mood'][key]['TEXT'] for key in sorted(grace['mood'])]
                        self.genre = [grace['genre'][key]['TEXT'] for key in sorted(grace['genre'])]
                        self.tempo = [grace['tempo'][key]['TEXT'] for key in sorted(grace['tempo'])]
                except Exception as e:
                    # urllib.error.URLError "getaddrinfo failed"
                    self.__class__.logger.warn('%s  %s', type(e), e)
                upd.emit()

        def gn_upd():
            if self.__class__.engine.lfm_login() is not None:
                self.__class__.interface.index()

        def gn_end():
            self.__correct_lfm()

        if not self._corrected_gn:
            harkfm.Util.thread(gn_do, gn_upd, gn_end)
            self._corrected_gn = True
        else:
            self.__correct_lfm()

    def __correct_lfm(self):
        lfm_network = self.__class__.engine.lfm_login()
        if lfm_network is None:
            return
        if self._corrected_lfm:
            return
        self._corrected_lfm = True

        lfm_count = 0

        def lfm_end():
            nonlocal lfm_count
            lfm_count += 1
            if lfm_count >= 3:  # wait on all artist/track/album
                if self.__class__.engine.lfm_login() is not None:
                    self.__class__.interface.index()

        def lfm_do_artist(upd):
            nonlocal lfm_network
            if self.artist:
                try:
                    # Do pylast.Artist functions manually to reduce API hits
                    artist = pylast._Request(lfm_network, 'artist.getInfo', {
                        'artist': self.artist,
                        'autocorrect': 1,
                        'username': lfm_network.username
                    }).execute(False)
                    props = {
                        'corrected': pylast._extract(artist, 'name'),
                        'url': pylast._extract(artist, 'url'),
                        'img': pylast._extract_all(artist, 'image')[-2],
                        'listeners': pylast._number(pylast._extract(artist, 'listeners')),
                        'plays_global': pylast._number(pylast._extract(artist, 'playcount')),
                        'similar': [{
                            'name': pylast._extract(a, 'name'),
                            'url': pylast._extract(a, 'url'),
                            'img': pylast._extract_all(a, 'image')[-2]
                        } for a in artist.getElementsByTagName('similar')[0].getElementsByTagName('artist')[:4]],
                        'tags': [{
                            'name': pylast._extract(t, 'name'),
                            'url': pylast._extract(t, 'url')
                        } for t in artist.getElementsByTagName('tag')[:5]],
                        'wiki': pylast._extract(artist, 'summary'),
                        'plays': pylast._number(pylast._extract(artist, 'userplaycount')),
                    }
                    for prop in props:
                        if props[prop]:
                            setattr(self, [p for p in dir(self) if 'artist' in p and p.endswith(prop)][0], props[prop])
                except Exception as e:
                    self.__class__.logger.warn('%s  %s', type(e), e)
        harkfm.Util.thread(lfm_do_artist, None, lfm_end)

        def lfm_do_track(upd):
            nonlocal lfm_network
            if self.artist and self.track:
                self.track_loved = False
                try:
                    # Do pylast.Track functions manually to reduce API hits
                    track = pylast._Request(lfm_network, 'track.getInfo', {
                        'track': self.track,
                        'artist': self.artist,
                        'autocorrect': 1,
                        'username': lfm_network.username
                    }).execute(False)
                    props = {
                        'corrected': pylast._extract(track, 'name'),
                        'url': pylast._extract(track, 'url'),
                        'wiki': pylast._extract(track, 'summary'),
                        'duration': pylast._number(pylast._extract(track, 'duration')) / 1000,
                        'plays': pylast._number(pylast._extract(track, 'userplaycount')),
                        'loved': bool(pylast._number(pylast._extract(track, 'userloved'))),
                        'tags': [{
                            'name': pylast._extract(t, 'name'),
                            'url': pylast._extract(t, 'url')
                         } for t in track.getElementsByTagName('tag')[:5]]
                    }
                    for prop in props:
                        if props[prop]:
                            setattr(self, [p for p in dir(self) if 'track' in p and p.endswith(prop)][0], props[prop])
                except Exception as e:
                    self.__class__.logger.warn('%s  %s', type(e), e)
        harkfm.Util.thread(lfm_do_track, None, lfm_end)

        def lfm_do_album(upd):
            nonlocal lfm_network
            if self.artist and self.album:
                try:
                    # Do pylast.Album functions manually to reduce API hits
                    album = pylast._Request(lfm_network, 'album.getInfo', {
                        'artist': self.artist,
                        'album': self.album,
                        'autocorrect': 1,
                        'username': lfm_network.username
                    }).execute(False)
                    props = {
                        'corrected': pylast._extract(album, 'name'),
                        'img': pylast._extract_all(album, 'image')[-2],
                        'url': pylast._extract(album, 'url')
                    }
                    for prop in props:
                        if props[prop]:
                            setattr(self, [p for p in dir(self) if 'album' in p and p.endswith(prop)][0], props[prop])
                except Exception as e:
                    self.__class__.logger.warn('%s  %s', type(e), e)
        harkfm.Util.thread(lfm_do_album, None, lfm_end)

    def listen(self):
        if not self.listened:
            lfm_network = self.__class__.engine.lfm_login()
            try:
                lfm_network.update_now_playing(self.artist, self.track, self.album)
                self.listened = int(time.time())
                return True
            except Exception as e:
                self.__class__.logger.warn('%s  %s', type(e), e)
        return False

    def scrobble(self):
        lfm_network = self.__class__.engine.lfm_login()

        timestamp = self.start + self.track_duration
        if timestamp > time.time():  # prevent future scrobbles
            timestamp = int(time.time())

        # Scrobble
        try:
            lfm_network.scrobble(self.artist, self.track, timestamp, self.album)
            return True
        except Exception as e:
            self.__class__.logger.warn('%s  %s', type(e), e)
        return False

    def love(self):
        lfm_network = self.__class__.engine.lfm_login()
        track = pylast.Track(self.artist, self.track, lfm_network, lfm_network.username)
        try:
            track.love()
            self.track_loved = True
            return True
        except Exception as e:
            self.__class__.logger.warn('%s  %s', type(e), e)
        return False

    def unlove(self):
        lfm_network = self.__class__.engine.lfm_login()
        track = pylast.Track(self.artist, self.track, lfm_network, lfm_network.username)
        try:
            track.unlove()
            self.track_loved = False
            return True
        except Exception as e:
            self.__class__.logger.warn('%s  %s', type(e), e)
        return False
