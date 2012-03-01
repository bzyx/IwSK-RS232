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
            "brak pliku"

    def save(self):
        with open(self.configName, "wb") as fileConfig:
            self.serialDict = self.serial.getSettingsDict()
            cPickle.dump(self.serialDict, fileConfig)
            Config.serial.applySettingsDict(self.serialDict)

    def load(self):
        with open(self.configName, "rb") as fileConfig:
            self.serialDict = cPickle.load(fileConfig)
            Config.serial.applySettingsDict(self.serialDict)

if __name__ == "__main__":
    configTest = Config()
    print configTest.serial
    configTest.save()
    configTest.load()
    print configTest.serialDict
    # configTest.serial.baudrate = 19200
    # configTest.save()
    # del configTest
    # configTestFile = Config()
    # configTestFile.load()
    # print configTestFile.serial
