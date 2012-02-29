import cPickle
from serial import Serial

class Config (object):
    """Default configuration for programing."""

    configName = "config.db"
    serial = Serial(0)

    def __init__(self):
        super(Config, self).__init__()
        try:
            self.load()
        except IOError:
            "brak pliku"

    def save(self):
        with open(self.configName, "wb") as fileConfig:
            setting = self.serial.getSettingsDict()
            cPickle.dump(setting, fileConfig)

    def load(self):
        with open(self.configName, "rb") as fileConfig:
            setting = cPickle.load(fileConfig)
        self.serial.applySettingsDict(setting)

if __name__ == "__main__":
    conf = Config()
    print conf.serial
