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
        if unicode(self.ui.i_terminator_comboBox.currentText()) == u"własny":
            self.ui.i_itsTerminator_lineEdit.setText(self.myConfig.serialDict.get('itsTerminator', ''))
            self.ui.i_howMuchChars_spinBox.setValue(len(str(self.ui.i_itsTerminator_lineEdit.text())))
        # except KeyError:
        #     self.ui.i_portName_comboBox.setCurrentIndex(0)
        self.byteSizeList[byteSizeIndex].setChecked(True)
        self.paritiesList[paritiesIndex].setChecked(True)
        self.stopBitsList[stopBitsIndex].setChecked(True)
        self.bufferRecived = ' '

        self.ui.btn_open.clicked.connect(self.openPort)
        self.ui.btn_close.clicked.connect(self.closePort)
        self.ui.btn_save.clicked.connect(self.save)
        self.ui.btn_clear_recived.clicked.connect(self.ui.o_recived_plainTextEdit.clear)
        self.ui.btn_clear_send.clicked.connect(self.ui.o_send_plainTextEdit.clear)
        self.ui.btn_send.clicked.connect(self.send)
        self.ui.btn_pingFunction.clicked.connect(self.ping)
        # self.ui.i_howMuchChars_spinBox.valueChanged(int).connect(self.changedSizeTerminator)
        QtCore.QObject.connect(self.ui.i_howMuchChars_spinBox, QtCore.SIGNAL("valueChanged(int)"), self.changedSizeTerminator)
        self.recivedTimer.timeout.connect(self.recived)

    def changedSizeTerminator(self, howMuch):
        self.ui.i_itsTerminator_lineEdit.setMaxLength(howMuch)

    def openPort(self):
        Config.serial.open()
        self.recivedTimer.start(1000)

    def closePort(self):
        self.recivedTimer.stop()
        Config.serial.close()

    def recived(self):
        if  Config.serial.inWaiting():
            print "jestem"
            recivedText = Config.serial.read(Config.serial.inWaiting())
            self.bufferRecived += recivedText
            print repr(self.bufferRecived)
            self.bufferRecived, isTerminator = self.searchTerminator(self.bufferRecived)
            print repr(self.bufferRecived)
            if isTerminator:
                self.ui.o_recived_plainTextEdit.appendPlainText(self.bufferRecived)
                if re.search(r'^ ?p<[0-2][0-9](:[0-5][0-9]){2}>!$', self.bufferRecived):
                    print 'jest'
                    sendRecivePing = "rp<%s>!" % (time.strftime('%X'))
                    print repr(sendRecivePing + self.terminatorList[self.myConfig.serialDict.get('terminator', 'CR')])
                    Config.serial.write(sendRecivePing + self.terminatorList[self.myConfig.serialDict.get('terminator', 'CR')])
                self.bufferRecived = ''

    def ping(self):
        sendPing = "p<%s>!" % (time.strftime('%X'))
        Config.serial.write(sendPing + self.terminatorList[self.myConfig.serialDict.get('terminator', 'CR')])

    def send(self):
        terminator = self.terminatorList[self.myConfig.serialDict.get('terminator', 'CR')]
        sendText = str(self.ui.lineEdit.text())
        if self.myConfig.serialDict.get('automaticTerminator', True):
            sendText += terminator
            Config.serial.write(sendText)
            sendText, isTerminator = self.searchTerminator(sendText)
            self.ui.o_send_plainTextEdit.appendPlainText(sendText)
        else:
            sendText, isTerminator = self.searchTerminator(sendText)
            self.sendTextBuffor += sendText
            if isTerminator:
                self.ui.o_send_plainTextEdit.appendPlainText(self.sendTextBuffor)
                Config.serial.write(self.sendTextBuffor + terminator)
                self.sendTextBuffor = ''
        self.ui.lineEdit.clear()

    def searchTerminator(self, text):
        terminator = self.terminatorList[self.myConfig.serialDict.get('terminator', 'CR')]

        if terminator in text:
            indexFind = True
        elif ("%s" % repr(terminator)[1:-1]) in text:
            terminator = "%s" % repr(terminator)[1:-1]
            terminator = repr(terminator)[1:-1]
            indexFind = True
        else:
            indexFind = False

        text = re.split(terminator, text)[0]
        return (text, indexFind)

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
        self.myConfig.serialDict['terminator'] = unicode(self.ui.i_terminator_comboBox.currentText())
        if unicode(self.ui.i_terminator_comboBox.currentText()) == u"własny":
            self.myConfig.serialDict['itsTerminator'] = str(self.ui.i_itsTerminator_lineEdit.text())
            self.terminatorList[u'własny'] = self.myConfig.serialDict['itsTerminator']
        self.myConfig.save()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myApp = MyDialog()
    myApp.show()
    sys.exit(app.exec_())
