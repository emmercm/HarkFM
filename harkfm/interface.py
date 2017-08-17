import json
import logging
import os
import sys
import urllib
import webbrowser

from PyQt5.QtCore import QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineView

import genshi.core
import genshi.template
import pylast

import harkfm


class Interface(object):
    _last_page = ''

    loader = None
    qMainWindow = None
    qtDesigner = None

    logger = None

    def __init__(self, qMainWindow=None, qtDesigner=None):
        if self.__class__.logger is None:
            self.__class__.logger = logging.getLogger('root')

        if self.__class__.loader is None:
            self.__class__.loader = genshi.template.TemplateLoader(
                os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'www')),
                auto_reload=True
            )

        if self.__class__.qMainWindow is None and qMainWindow is not None:
            self.__class__.qMainWindow = qMainWindow

        if self.__class__.qtDesigner is None and qtDesigner is not None:
            self.__class__.qtDesigner = qtDesigner

            class WebEnginePage(QWebEnginePage):
                updated = pyqtSignal(str, float, str)

                def javaScriptConsoleMessage(self, level, msg, line, source):
                    harkfm.Interface.logger.debug('%s:%s  %s', source, line, msg)

                def acceptNavigationRequest(self, url, type, is_main_frame):
                    if type == QWebEnginePage.NavigationTypeLinkClicked:
                        webbrowser.open(url.toString())
                        return False
                    return True

                # Turn a jQuery.serialize() query into a dict
                def _deserialize(self, query):
                    form = {}
                    query = query.split('&')
                    for val in query:
                        val = val.split('=')
                        form[urllib.parse.unquote(val[0])] = urllib.parse.unquote(val[1])
                    return form

                @pyqtSlot()
                def update(self):
                    if engine.current is not None:
                        self.updated.emit(engine.current.elapsed, engine.current.percent, engine.current.remaining)

                @pyqtSlot()
                def queued(self):
                    queued = 0
                    if engine.current is not None:
                        queued = engine.current.queued
                    self.updated.emit(sys._getframe().f_code.co_name, queued)

                @pyqtSlot()
                def love(self):
                    engine.current.love()
                    interface = harkfm.Interface()
                    interface.index()

                @pyqtSlot()
                def unlove(self):
                    engine.current.unlove()
                    interface = harkfm.Interface()
                    interface.index()

                @pyqtSlot(str)
                def login(self, query):
                    form = self._deserialize(query)
                    storage = harkfm.Storage()
                    api_key = harkfm.Engine.config['apis']['last.fm']['key']
                    api_secret = harkfm.Engine.config['apis']['last.fm']['secret']
                    try:
                        network = pylast.get_lastfm_network(api_key, api_secret)
                        session_key = pylast.SessionKeyGenerator(network).get_session_key(form['username'],  pylast.md5(form['password']))
                        storage.config_set('apis/last.fm/session_key', session_key)
                        interface = harkfm.Interface()
                        interface.index()
                    except Exception as e:
                        harkfm.Interface.logger.error('%s  %s', type(e), e)

                @pyqtSlot()
                def logout(self):
                    engine = harkfm.Engine()
                    engine.lfm_logout()

                @pyqtSlot(str)
                def save_settings(self, form):
                    form = json.loads(form)
                    storage = harkfm.Storage()
                    for key in form:
                        if type(form[key]) is str and form[key].isdigit():
                            form[key] = int(form[key])
                        storage.config_set('settings/' + key, form[key])
                    interface = harkfm.Interface()
                    interface.index()

            # Set custom page
            page = WebEnginePage(self.QWebEngineView)
            page.profile().setHttpCacheType(QWebEngineProfile.NoCache)
            self.QWebEngineView.setPage(page)

            # Set custom channel
            channel = QWebChannel(page)
            channel.registerObject('py', page)
            page.setWebChannel(channel)

            engine = harkfm.Engine()  # init harkfm.Engine
            lfm_network = engine.lfm_login()
            if lfm_network is None:
                self.login()
            else:
                self.index()

    @property
    def QWebEngineView(self):
        for prop in dir(self.__class__.qtDesigner):
            if type(getattr(self.__class__.qtDesigner, prop)) is QWebEngineView:
                return getattr(self.__class__.qtDesigner, prop)
        return None

    @property
    def QWebEnginePage(self):
        view = self.QWebEngineView
        if view:
            return view.page()
        return None

    def login(self):
        self.__render('login.html')

    def index(self):
        self.__render('index.html')

    def __render(self, file):
        engine = harkfm.Engine()
        template = self.__class__.loader.load(file)
        search_path = 'file:///' + self.__class__.loader.search_path[0].replace('\\', '/') + '/'
        html = template.generate(
            current=engine.current,
            lastfm=engine.lfm_props(),
            config=harkfm.Storage.config
        ).render('html', doctype='html')
        self.QWebEngineView.setHtml(html, QUrl(search_path))
        self.__class__._last_page = file
