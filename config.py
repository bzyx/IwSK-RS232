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

    def save(self):
        with open(self.configName, "wb") as fileConfig:
            # self.serialDict = Config.serial.getSettingsDict()
            cPickle.dump(self.serialDict, fileConfig)
            try:
                Config.serial.port = self.serialDict['port']
            except KeyError:
                pass
            Config.serial.applySettingsDict(self.serialDict)

    def load(self):
        with open(self.configName, "rb") as fileConfig:
            self.serialDict = cPickle.load(fileConfig)
            try:
                Config.serial.port = self.serialDict['port']
            except KeyError:
                pass
            Config.serial.applySettingsDict(self.serialDict)

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
