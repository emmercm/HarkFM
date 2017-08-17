#!/usr/bin/env python3

import logging
import os
import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
import PyQt5.uic

import harkfm


formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname).4s] [%(filename)s:%(lineno)03d]  %(message)s',
    datefmt='%H:%M:%S'
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger('root')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = QApplication(sys.argv)
window = QMainWindow(flags=Qt.Window)
ui = PyQt5.uic.loadUi(os.path.join(os.path.dirname(sys.argv[0]), 'harkfm/interface.ui'), window)

# Init the interface
interface = harkfm.Interface(window, ui)
# Start track scanner
scanner = harkfm.Scanner()

window.show()
exit_code = app.exec_()
if exit_code == 0:
    engine = harkfm.Engine()
    engine.scrobble()
    while engine.scrobbling:
        time.sleep(0.1)
sys.exit(exit_code)
