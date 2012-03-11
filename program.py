#-*-coding: utf8-*-
import sys

from PyQt4 import QtGui, QtCore
from ui.iwsk import Ui_Dialog
from config import Config
from serial.tools import list_ports
import time
import re
import collections


# TODO: add automatic terminator option
class MyDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.myConfig = Config()
        self.sendTextBuffor = ''
        self.protocolOptionDict = {'Brak': ' ', 'CTRL-S/CTRL-Q': 'xonxoff', 'DTR/DSR': 'dsrdtr', 'RTS/CTS': 'rtscts'}
        self.terminatorList = collections.OrderedDict([('CR', chr(13)), ('LF', chr(10)),  \
                ('CR, LF', chr(13) + chr(10)), ('brak', ''), (u'własny', '')])    # acii 10 -LF 13 -CR

        comPortsList = [portList[0] for portList in list_ports.comports()]
        self.recivedTimer = QtCore.QTimer(self)

        for baudRate in Config.serial.BAUDRATES:
            self.ui.i_baudRate_comboBox.addItem(repr(baudRate))

        for port in comPortsList:
            self.ui.i_portName_comboBox.addItem(port)

        for terminator in self.terminatorList.keys():
            self.ui.i_terminator_comboBox.addItem(terminator)

        for protocol in self.protocolOptionDict.keys():
            self.ui.i_protocol_comboBox.addItem(protocol)

        self.byteSizeList = [self.ui.i_word_5bits_radio, \
                self.ui.i_word_6bits_radio, \
                self.ui.i_word_7bits_radio, \
                self.ui.i_word_8bits_radio]

        self.paritiesList = [self.ui.i_parityNone_radio, \
                self.ui.i_parityEven_radio, \
                self.ui.i_parityOdd_radio]

        self.stopBitsList = [self.ui.i_stopBit1_radio, \
                self.ui.i_stopBit15_radio, \
                self.ui.i_stopBit2_radio]

        byteSizeIndex = Config.serial.BYTESIZES.index(self.myConfig.serialDict['bytesize'])
        paritiesIndex = Config.serial.PARITIES.index(self.myConfig.serialDict['parity'])
        stopBitsIndex = Config.serial.STOPBITS.index(self.myConfig.serialDict['stopbits'])
        timeoutConfigValue = self.myConfig.serialDict['timeout']

        if timeoutConfigValue:
            self.ui.i_timeout_spinBox.setValue(timeoutConfigValue)

        self.ui.i_baudRate_comboBox.setCurrentIndex(self.ui.i_baudRate_comboBox.\
                findText(repr(self.myConfig.serialDict['baudrate'])))
        # nie zrobic tego w configu??
        self.ui.i_terminator_comboBox.setCurrentIndex(self.ui.i_terminator_comboBox.\
                findText(self.myConfig.serialDict.get('terminator', 'CR')))
        # try:
        self.ui.i_portName_comboBox.setCurrentIndex(self.myConfig.serialDict.get('port', 0))
        self.ui.i_automaticTerminator_checkBox.setChecked(self.myConfig.serialDict.get('automaticTerminator', True))
        # except KeyError:
        #     self.ui.i_portName_comboBox.setCurrentIndex(0)
        self.byteSizeList[byteSizeIndex].setChecked(True)
        self.paritiesList[paritiesIndex].setChecked(True)
        self.stopBitsList[stopBitsIndex].setChecked(True)
        self.bufferRecived = ' '

        self.ui.btn_open.clicked.connect(self.openPort)
        self.ui.btn_close.clicked.connect(Config.serial.close)
        self.ui.btn_save.clicked.connect(self.save)
        self.ui.btn_clear_recived.clicked.connect(self.ui.o_recived_plainTextEdit.clear)
        self.ui.btn_clear_send.clicked.connect(self.ui.o_send_plainTextEdit.clear)
        self.ui.btn_send.clicked.connect(self.send)
        self.ui.btn_pingFunction.clicked.connect(self.ping)
        self.recivedTimer.timeout.connect(self.recived)

    def openPort(self):
        Config.serial.open()
        self.recivedTimer.start(1000)

    def recived(self):
        if  Config.serial.inWaiting():
            self.bufferRecived = Config.serial.read(Config.serial.inWaiting())
            self.ui.o_recived_plainTextEdit.appendPlainText(self.bufferRecived)
            if re.search(r'^p<[0-2][0-9](:[0-5][0-9]){2}>!$', self.bufferRecived):
                sendRecivePing = "rp<%s>!" % (time.strftime('%X'))
                Config.serial.write(sendRecivePing)

    def ping(self):
        sendPing = "p<%s>!" % (time.strftime('%X'))
        Config.serial.write(sendPing)

    def send(self):
        sendText = str(self.ui.lineEdit.text())
        if self.myConfig.serialDict.get('automaticTerminator', True):
            sendText.append(self.terminatorList[self.i_terminator_comboBox.currentText()])
            Config.serial.write(sendText)
            self.ui.o_send_plainTextEdit.appendPlainText(sendText)
        else:
            sendText, isTerminator = self.searchTerminator(sendText)
            print sendText, isTerminator
            self.sendTextBuffor += sendText
            if isTerminator:
                self.ui.o_send_plainTextEdit.appendPlainText(self.sendTextBuffor)
                Config.serial.write(self.sendTextBuffor)
                self.sendTextBuffor = ''
        self.ui.lineEdit.clear()

    def searchTerminator(self, text):
        terminator = self.terminatorList[self.myConfig.serialDict.get('terminator', u'CR')]
        print terminator
        indexFind = text.find(repr(terminator)[1:-1])
        if indexFind == -1:
            return (text, False)
        else:
            return (text[:indexFind], True)

    def save(self):
        for clear in self.protocolOptionDict.values():
            self.myConfig.serialDict[clear] = False
        if(self.ui.i_protocol_comboBox.currentIndex() != 0):
            self.myConfig.serialDict[self.protocolOptionDict[\
                    str(self.ui.i_protocol_comboBox.currentText())]] = True

        self.myConfig.serialDict['port'] = self.ui.i_portName_comboBox.currentIndex()   # +1
        self.myConfig.serialDict['baudrate'] = int(self.ui.i_baudRate_comboBox.currentText())
        for byteSize in self.byteSizeList:
            if(byteSize.isChecked()):
                self.myConfig.serialDict['bytesize'] = int(byteSize.text())
        for parity in self.paritiesList:
            if(parity.isChecked()):
                self.myConfig.serialDict['parity'] = Config.serial.PARITIES[self.paritiesList.index(parity)]
        for stopBit in self.stopBitsList:
            if(stopBit.isChecked()):
                self.myConfig.serialDict['stopbits'] = Config.serial.STOPBITS[self.stopBitsList.index(stopBit)]
        if self.ui.i_timeout_spinBox.value():
            self.myConfig.serialDict['timeout'] = self.ui.i_timeout_spinBox.value()
        else:
            self.myConfig.serialDict['timeout'] = None
        self.myConfig.serialDict['automaticTerminator'] = self.ui.i_automaticTerminator_checkBox.isChecked()
        self.myConfig.serialDict['terminator'] = str(self.ui.i_terminator_comboBox.currentText())
        self.myConfig.save()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myApp = MyDialog()
    myApp.show()
    sys.exit(app.exec_())
