from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os
import sys
import multiprocessing
"""
List of called modules
os
sys
csv
io
datetime
openpyxl
CoolProp
zipfile
shutil
sympy
copy
numpy
math
lxml
sklearn
CapillaryUI
time
appdirs
scipy
itertools
matplotlib
multiprocessing
random
psychrolib
* files in this directory
"""
class ThreadProgress(QThread):
    mysignal = pyqtSignal(int)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
    def run(self):
        import importlib
        list_of_modules = ['os',
                           'sys',
                           'csv',
                           'io',
                           'datetime',
                           'openpyxl',
                           'CoolProp',
                           'zipfile',
                           'shutil',
                           'sympy',
                           'copy',
                           'numpy',
                           'math',
                           'lxml',
                           'sklearn',
                           'CapillaryUI',
                           'time',
                           'appdirs',
                           'itertools',
                           'scipy',
                           'matplotlib',
                           'multiprocessing',
                           'random',
                           'psychrolib',
                           ]
        files = [f[:-3] for f in os.listdir('.') if (f[-3:].lower() == '.py')]
        list_of_modules += files
        list_of_modules += files        
        length = len(list_of_modules)
        for i,module in enumerate(list_of_modules):
            z = importlib.import_module(module)
            self.mysignal.emit(int((i+1)/length*100))
        
class Splash(QWidget):
    main_windows = []
    def __init__(self, parent = None):
        super(Splash, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        pixmap = QPixmap("photos/splash.png")
        self.splash_image = QLabel(self)
        self.splash_image.setPixmap(pixmap.scaled(518, 517))
        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        vbox = QVBoxLayout()
        vbox.addWidget(self.splash_image)
        vbox.addWidget(self.pbar)
        self.setLayout(vbox)
        self.adjustSize()
        screenGeometry = QApplication.desktop().geometry()
        x = int((screenGeometry.width() - self.width()) / 2)
        y = int((screenGeometry.height() - self.height()) / 2)
        self.move(x, y)
        progress = ThreadProgress(self)
        progress.mysignal.connect(self.progress)
        progress.start()
        
    @pyqtSlot(int)
    def progress(self, finished):
        self.pbar.setValue(finished)
        if finished == 100:
            self.hide()
            self.start_main()
    
    def start_main(self,style=None):
        from MainWindow import MainWindow
        main_window = MainWindow()
        if style != None:
            main_window.setStyleSheet(QStyleFactory.create(style))
        main_window.show()
        main_window.close_signal_to_main.connect(self.close)
        main_window.restart_signal_to_main.connect(self.start_main)
        main_window.change_style_signal_to_main.connect(self.start_main)
        self.main_windows.append(main_window)

def main():
    app=QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon('photos/icon.png'))
    window = Splash()
    window.show()
    app.exec_()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except Exception as why:
        print(why)

