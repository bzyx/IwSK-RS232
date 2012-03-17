#-*-coding: utf8-*-
import sys

from PyQt4 import QtGui, QtCore
from collections import OrderedDict
from serial.tools import list_ports

import time
import re

from config import Config
from ui.iwsk import Ui_Dialog


# TODO: add automatic terminator option
class MyDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.myConfig = Config()
        # bufor na tekst do wysłania
        self.sendTextBuffor = ''
        
        # bufor na wartości odczytane
        self.bufferRecived = ' '
        # Opcje wyboru sterowania magistrali
        self.protocolOptionDict = {'Brak': ' ', 'CTRL-S/CTRL-Q': 'xonxoff', 'DSR/DTR': 'dsrdtr', 'RTS/CTS': 'rtscts'}
        # Terminatory standardowe + terminator w�asny
        # ASCII 10 -LF 13 -CR
        self.treminatorTypes = OrderedDict([('CR', chr(13)), ('LF', chr(10)), \
                                                       ('CR, LF', chr(13) + chr(10)), \
                                                       ('brak', ''), \
                                                       (u'własny', '')])    

        # Tworzymy lista dostępnych w systemie portów COM
        comPortsList = [portList[0] for portList in list_ports.comports()]
        
        #Timmer do odbioru danych/powoduje zap�tlenie programu
        self.recivedTimer = QtCore.QTimer(self)
        
        
        
        # Połączenie sygnałów/slotów - wewnętrzne sprawy Qt
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
        self.ui.i_terminator_comboBox.currentIndexChanged[str].connect(self.terminatorChanged)

        # Tworzenie listy obsługiwanych wartości szybkości transmisji
        for baudRate in Config.serial.BAUDRATES:
            self.ui.i_baudRate_comboBox.addItem(repr(baudRate))

        # Tworzenie listy dostępnych portów COM - dla intefejsu użytkownika
        for port in comPortsList:
            self.ui.i_portName_comboBox.addItem(port)
        
        # Dodajemy możliwe typy terminatora
        for terminator in self.treminatorTypes.keys():
            self.ui.i_terminator_comboBox.addItem(terminator)

        # Dodajemy listę typów sterowania transmisją 
        for protocol in self.protocolOptionDict.keys():
            self.ui.i_protocol_comboBox.addItem(protocol)

        # Tworzymy listy obiektów intefejsu użytkownika
        # reprezentująch parametry transmisji. 
        # W celu ułatwienia zarz�dzania transmisją.
        # Długś słowa
        self.byteSizeList = [self.ui.i_word_5bits_radio, \
                self.ui.i_word_6bits_radio, \
                self.ui.i_word_7bits_radio, \
                self.ui.i_word_8bits_radio]

        # Parzystość
        self.paritiesList = [self.ui.i_parityNone_radio, \
                self.ui.i_parityEven_radio, \
                self.ui.i_parityOdd_radio]

        # Liczba bitiów stopu
        self.stopBitsList = [self.ui.i_stopBit1_radio, \
                self.ui.i_stopBit15_radio, \
                self.ui.i_stopBit2_radio]

        # Wczytujemy dane z poprzedniej konfiguracji jeśli taka była
        timeoutConfigValue = self.myConfig.serialDict['timeout']

        # Aktualizujemy interfejs użytkownika wczytanymi wartośćiami
        if timeoutConfigValue:
            self.ui.i_timeout_spinBox.setValue(timeoutConfigValue)
        self.ui.i_baudRate_comboBox.setCurrentIndex(self.ui.i_baudRate_comboBox.\
                findText(repr(self.myConfig.serialDict['baudrate'])))
        self.ui.i_terminator_comboBox.setCurrentIndex(self.ui.i_terminator_comboBox.\
                findText(self.myConfig.serialDict.get('terminator', 'CR')))
        # protocolSet = lambda lista:
        # self.ui.i_protocol_comboBox.setCurrentIndex(self.ui.i_protocol_comboBox.\
        #         findText(self.myConfig.serialDict.get('p
        # try:
        self.ui.i_portName_comboBox.setCurrentIndex(self.myConfig.serialDict.get('port', 0))
        self.ui.i_automaticTerminator_checkBox.setChecked(self.myConfig.serialDict.get('automaticTerminator', True))
        if unicode(self.ui.i_terminator_comboBox.currentText()) == u"własny":
            self.ui.i_itsTerminator_lineEdit.setText(self.myConfig.serialDict.get('itsTerminator', ''))
            self.ui.i_howMuchChars_spinBox.setValue(len(str(self.ui.i_itsTerminator_lineEdit.text())))
        # except KeyError:
        #     self.ui.i_portName_comboBox.setCurrentIndex(0)
        
        # Odczytanie i ustwienie wybranej wartości długości słowa, parzystości, liczby bitów stopu
        byteSizeIndex = Config.serial.BYTESIZES.index(self.myConfig.serialDict['bytesize'])
        paritiesIndex = Config.serial.PARITIES.index(self.myConfig.serialDict['parity'])
        stopBitsIndex = Config.serial.STOPBITS.index(self.myConfig.serialDict['stopbits'])
        
        self.byteSizeList[byteSizeIndex].setChecked(True)
        self.paritiesList[paritiesIndex].setChecked(True)
        self.stopBitsList[stopBitsIndex].setChecked(True)
        
        # Odczytanie i ustawienie wartości o sposobie zarządzania transmisją
        if self.myConfig.serialDict['dsrdtr']:
            protocolIndex = 2
        elif self.myConfig.serialDict['rtscts']:
            protocolIndex = 3
        elif self.myConfig.serialDict['xonxoff']:
            protocolIndex = 1
        else:
            protocolIndex = 0
        self.ui.i_protocol_comboBox.setCurrentIndex(protocolIndex)


    def dtrRts(self):
        Config.serial.setRTS(False)
        Config.serial.setDTR(False)
        if Config.serial.dsrdtr:
            print "jeden"
            self.dtrRtsWrite = Config.serial.setDTR
        elif Config.serial.rtscts:
            print "dwa"
            self.dtrRtsWrite = Config.serial.setRTS
        elif Config.serial.xonxoff:
            print "trzy"
            self.dtrRtsWrite = Config.serial.setXON
        else:
            self.dtrRtsWrite = lambda tekst: tekst

    @QtCore.pyqtSlot()
    def changedSizeTerminator(self, howMuch):
        self.ui.i_itsTerminator_lineEdit.setMaxLength(howMuch)
        
    @QtCore.pyqtSlot()
    def openPort(self):
        Config.serial.open()
        self.dtrRts()
        self.dtrRtsWrite(True)
        # self.dtrRtsWrite(True)
        self.recivedTimer.start(1000)
        print "Port Opened"

    @QtCore.pyqtSlot()
    def closePort(self):
        self.recivedTimer.stop()
        Config.serial.close()
        print "Port Closed"

    @QtCore.pyqtSlot()
    def recived(self):
        # TODO: ogarnac xonxoff
        # xonxoff = False
        print Config.serial.getCTS(), Config.serial.getDSR(), Config.serial.getRtsCts(), Config.serial.getRtsToggle()
        if  Config.serial.inWaiting():
            recivedText = Config.serial.read(Config.serial.inWaiting())
            # if recivedText.find(
            self.bufferRecived += recivedText
            self.bufferRecived, isTerminator = self.searchTerminator(self.bufferRecived)
            print repr(self.bufferRecived)
            if isTerminator:
                self.ui.o_recived_plainTextEdit.appendPlainText(self.bufferRecived)
                if re.search(r'^ ?p<[0-2][0-9](:[0-5][0-9]){2}>!$', self.bufferRecived):
                    sendRecivePing = "rp<%s>!" % (time.strftime('%X'))
                    print repr(sendRecivePing + self.treminatorTypes[self.myConfig.serialDict.get('terminator', 'CR')])
                    Config.serial.write(sendRecivePing + self.treminatorTypes[self.myConfig.serialDict.get('terminator', 'CR')])
                self.bufferRecived = ''

    @QtCore.pyqtSlot(str)
    def terminatorChanged(self, itemName):
        shouldShow = False
        if itemName == u"własny":
            shouldShow = True
            
        self.ui.i_howMuchChars_spinBox.setVisible(shouldShow)
        self.ui.i_itsTerminator_lineEdit.setVisible(shouldShow)
        self.ui.customTermator.setVisible(shouldShow)

    @QtCore.pyqtSlot()
    def ping(self):
        sendPing = "p<%s>!" % (time.strftime('%X'))
        Config.serial.write(sendPing + self.treminatorTypes[self.myConfig.serialDict.get('terminator', 'CR')])

    @QtCore.pyqtSlot()
    def send(self):
        if Config.serial.getDSR() or Config.serial.getCTS() or Config.serial.xonxoff:
            # self.dtrRtsWrite(False)
            terminator = self.treminatorTypes[self.myConfig.serialDict.get('terminator', 'CR')]
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
            # self.dtrRtsWrite(True)

    def searchTerminator(self, text):
        terminator = self.treminatorTypes[self.myConfig.serialDict.get('terminator', 'CR')]

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
    
    @QtCore.pyqtSlot()
    def save(self):
        if Config.serial.isOpen():
            QtGui.QMessageBox.warning(None, u"RS-232", u"Należy zamknąć i otworzyć port, aby zmiany zostały wporawdzone.", \
                                      buttons=QtGui.QMessageBox.Ok, defaultButton=QtGui.QMessageBox.NoButton)
        for clear in self.protocolOptionDict.values():
            self.myConfig.serialDict[clear] = False
        if self.ui.i_protocol_comboBox.currentIndex() != 0:
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
            self.treminatorTypes[u'własny'] = self.myConfig.serialDict['itsTerminator']
        self.myConfig.save()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myApp = MyDialog()
    myApp.show()
    sys.exit(app.exec_())
