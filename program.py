#-*-coding: utf8-*-
import sys

from PyQt4 import QtCore, QtGui
from ui.iwsk import Ui_Dialog
from config import Config


class MyDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        myConfig = Config()
        #QtCore.QObject.connect(self.ui.btn_open, QtCore.SIGNAL("clicked()"), myConfig.serial.open)
        #QtCore.QObject.connect(self.ui.btn_close, QtCore.SIGNAL("clicked()"), myConfig.serial.close)
        #QtCore.QObject.connect(self.ui.btn_save, QtCore.SIGNAL("clicked()"), myConfig.save)
        self.ui.btn_open.clicked.connect(myConfig.serial.open)
        self.ui.btn_close.clicked.connect(myConfig.serial.close)
        self.ui.btn_save.clicked.connect(myConfig.save)

        for baudRate in myConfig.serial.BAUDRATES:
            self.ui.i_baudRate_comboBox.addItem(repr(baudRate))

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myApp = MyDialog()
    myApp.show()
    sys.exit(app.exec_())
