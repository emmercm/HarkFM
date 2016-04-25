#!/usr/bin/env python3

import logging
import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow
from QtDesigner import Ui_MainWindow

import harkfm


formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname).4s] [%(filename)s:%(lineno)03d]  %(message)s',
    datefmt='%H:%M:%S'
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

app = QApplication(sys.argv)
window = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(window)

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
