from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import os, sys

FROM_ABOUT,_ = loadUiType(os.path.join(os.path.dirname(__file__),"ui_files/about.ui"))

class AboutWindow(QDialog, FROM_ABOUT):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.version.setText("1.3.7")
        # intially load images
        def images_loader(path,var_name,size):
            try:
                photo = QPixmap(path)
                photo = photo.scaledToWidth(size)
                setattr(self,var_name,photo)
            except:
                pass
        images_loader("photos/Large_icon.png",'Logo',96)
        
        self.about_label.setOpenExternalLinks(True)
        self.logo_label.setPixmap(self.Logo)

if __name__ == '__main__':
    def main():
        app=QApplication(sys.argv)
        app.setStyle('Fusion')
        window = AboutWindow()
        window.show()
        app.exec_()
    try:
        main()
    except Exception as why:
        print(why)

        