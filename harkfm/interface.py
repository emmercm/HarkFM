import copy
import math
import os
import sys
import time
import webbrowser

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWebKit import QWebElement
from PyQt5.QtWebKitWidgets import QWebPage

import genshi.core
import genshi.template
import pylast

import harkfm


class Interface(object):
    _last_page = ''

    loader = None
    qMainWindow = None
    qtDesigner = None

    def __init__(self, qMainWindow=None, qtDesigner=None):
        if self.__class__.loader is None:
            self.__class__.loader = genshi.template.TemplateLoader(
                os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'www')),
                auto_reload=True
            )
        if self.__class__.qMainWindow is None and qMainWindow is not None:
            self.__class__.qMainWindow = qMainWindow

        if self.__class__.qtDesigner is None and qtDesigner is not None:
            self.__class__.qtDesigner = qtDesigner
            self.__class__.qtDesigner.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
            self.__class__.qtDesigner.webView.page().linkClicked.connect(lambda link: webbrowser.open(link.toString()))

            self.__class__.qtDesigner.action_About.triggered.connect(self.on_about)

            engine = harkfm.Engine()  # init harkfm.Engine
            lfm_network = engine.lfm_login()
            if lfm_network is None:
                self.login()
            else:
                self.index()

    def login(self):
        self.__render('login.html')

    def index(self):
        self.__render('index.html')

    def __render(self, file):
        class Extensions(QObject):
            @QtCore.pyqtSlot(result=str)
            def elapsed(self):
                if engine.current is not None:
                    elapsed = math.floor(time.time() - engine.current.start)
                else:
                    elapsed = 0
                text = ''
                if elapsed > 3600:
                    text += str(math.floor(elapsed/3600)) + ':'
                text += str(math.floor(elapsed/60) % 60) + ':' + str(elapsed % 60).zfill(2)
                return text

            @QtCore.pyqtSlot(result=float)
            def percent(self):
                if engine.current is not None:
                    return min(100, round((time.time() - engine.current.start) / engine.current.track_duration * 100, 1))
                else:
                    return 0

            @QtCore.pyqtSlot(result=str)
            def remaining(self):
                if engine.current is not None:
                    remaining = math.ceil(engine.current.start + engine.current.track_duration - time.time())
                else:
                    remaining = 0
                text = '-'
                if remaining > 3600:
                    text += str(math.floor(remaining/3600)) + ':'
                text += str(math.floor(remaining/60) % 60) + ':' + str(remaining % 60).zfill(2)
                return text

            @QtCore.pyqtSlot(result=int)
            def listened(self):
                if engine.current is not None:
                    return engine.current.listened
                else:
                    return 0

            @QtCore.pyqtSlot(result=int)
            def queued(self):
                if engine.current is not None:
                    return engine.current.queued
                else:
                    return 0

            @QtCore.pyqtSlot()
            def love(self):
                engine.current.love()
                interface = harkfm.Interface()
                interface.index()

            @QtCore.pyqtSlot()
            def unlove(self):
                engine.current.unlove()
                interface = harkfm.Interface()
                interface.index()

            @QtCore.pyqtSlot(QWebElement)
            def login(self, form):
                storage = harkfm.Storage()
                lfm_username = form.findFirst('input[name=username]').evaluateJavaScript('this.value')
                lfm_password = pylast.md5(form.findFirst('input[name=password]').evaluateJavaScript('this.value'))
                api_key = harkfm.Engine.config['apis']['last.fm']['key']
                api_secret = harkfm.Engine.config['apis']['last.fm']['secret']
                try:
                    network = pylast.get_lastfm_network(api_key, api_secret)
                    session_key = pylast.SessionKeyGenerator(network).get_session_key(lfm_username, lfm_password)
                    storage.config_set('apis/last.fm/session_key', session_key)
                    interface = harkfm.Interface()
                    interface.index()
                except Exception as e:
                    print(e)

            @QtCore.pyqtSlot(QWebElement)
            def logout(self):
                engine = harkfm.Engine()
                engine.lfm_logout()

        ext = Extensions(self.__class__.qMainWindow)

        # Prep page variables
        engine = harkfm.Engine()
        current = copy.copy(engine.current)
        if current is not None:
            current._elapsed = ext.elapsed()
            current._percent = ext.percent()
            current._remaining = ext.remaining()
        lastfm = engine.lfm_props()

        template = self.__class__.loader.load(file)
        search_path = 'file:///' + self.__class__.loader.search_path[0].replace('\\', '/') + '/'
        html = template.generate(current=current, lastfm=lastfm).render('html', doctype='html')
        self.__class__.qtDesigner.webView.setHtml(html, QUrl(search_path))
        self.__class__.qtDesigner.webView.page().mainFrame().addToJavaScriptWindowObject('py', ext)
        self.__class__._last_page = file


    def on_about(self):
        button = self.__class__.qtDesigner.webView.page().mainFrame().findFirstElement('#button-about')
        if button is not None:
            button.evaluateJavaScript('this.click();')