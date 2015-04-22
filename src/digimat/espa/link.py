import time
import serial

# pyserial docs
# http://pyserial.sourceforge.net/pyserial_api.html

# list available ports
# python -m serial.tools.list_ports

# miniterm
# python -m serial.tools.miniterm <port name> [-h]


class Link(object):
    def __init__(self, name):
        self._logger=None
        if not name:
            name='espalink'
        self.setName(name)

    def setLogger(self, logger):
        self._logger=logger

    def setName(self, name):
        self._name=name

    @property
    def logger(self):
        return self._logger

    @property
    def name(self):
        return self._name

    def open(self):
        pass

    def reset(self):
        self.read()

    def close(self):
        pass

    def read(self):
        return None

    def write(self, data):
        return False


# see http://pyserial.sourceforge.net/pyserial_api.html#urls for url allowed syntax
class LinkSerial(Link):
    def __init__(self, name, url, baudrate=9600, parity='N', datasize=8, stopbits=1, rtscts=False):
        super(LinkSerial, self).__init__(name)
        self.setName(name)
        self._serial=None
        self._url=url
        self._baudrate=baudrate
        self._parity=parity
        self._datasize=datasize
        self._stopbits=stopbits
        self._rtscts=0
        if rtscts:
            self._rtscts=1
        self._reopenTimeout=0

    @classmethod
    def listPorts(cls):
        return serial.tools.list_ports.comports()

    def open(self):
        if self._serial:
            return True
        try:
            if time.time()>self._reopenTimeout:
                self._reopenTimeout=time.time()+15
                self.logger.info('open(%s)' % (self._url))

                s=serial.serial_for_url(self._url)
                s.baudrate=self._baudrate
                s.parity=self._parity
                s.stopbits=self._stopbits
                s.bytesize=self._datasize
                s.rtscts=self._rtscts
                s.timeout=0
                try:
                    s.writeTimeout=0
                except:
                    pass

                self._serial=s
                self.logger.info('port(%s) opened' % self._url)
                return True
        except:
            self.logger.exception('open()')
            #self.logger.error('open(%s) error' % self._url)
            self._serial=None

    def close(self):
        try:
            self.logger.info('close(%s)' % self._url)
            self._serial.close()
        except:
            pass
        self._serial=None

    def read(self, size=255):
        try:
            if self.open() and size>0:
                data=self._serial.read(size)
                if data:
                    return bytearray(data)
        except:
            self.logger.exception('read(%s)' % self._url)
            self.close()

    def write(self, data):
        try:
            if self.open():
                self._serial.write(data)
                return True
        except:
            self.logger.exception('write(%s)' % self._url)
            self.close()


if __name__=='__main__':
    pass

