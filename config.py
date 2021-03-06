#-*-coding: utf8-*-
import cPickle
from serial import Serial


class Config(object):
    """Default configuration for programing."""

    configName = "config.db"
    serial = Serial()

    def __init__(self):
        super(Config, self).__init__()
        try:
            self.load()
        except IOError:
            self.serialDict = Config.serial.getSettingsDict()
            print u"Brak pliku wczytano i załadowano dane domyślne"

    def save(self):
        with open(self.configName, "wb") as fileConfig:
            # self.serialDict = Config.serial.getSettingsDict()
            cPickle.dump(self.serialDict, fileConfig)
            try:
                Config.serial.port = self.serialDict['port']
            except KeyError:
                pass
            print u"Zapis zakończony powodzeniem"
            Config.serial.applySettingsDict(self.serialDict)
            print u"Dane załadowane"

    def load(self):
        with open(self.configName, "rb") as fileConfig:
            self.serialDict = cPickle.load(fileConfig)
            try:
                Config.serial.port = self.serialDict['port']
            except KeyError:
                pass
            print u"Dane poprawnie odczytane z pliku"
            Config.serial.applySettingsDict(self.serialDict)
            print u"Dane załadowane"

if __name__ == "__main__":
    configTest = Config()
    # configTest.load()
    # print configTest.serial
    # print configTest.serialDict
    # configTest.save()
    # configTest.load()
    print configTest.serialDict
    # configTest.serial.baudrate = 19200
    # configTest.save()
    # del configTest
    # configTestFile = Config()
    # configTestFile.load()
    # print configTestFile.serial
