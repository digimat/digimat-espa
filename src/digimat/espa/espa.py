import time
import struct
import serial
from threading import Event
import logging, logging.handlers

# pyserial docs
# http://pyserial.sourceforge.net/pyserial_api.html

# list available ports
# python -m serial.tools.list_ports

# miniterm
# python -m serial.tools.miniterm <port name> [-h]


ESPA_CLIENT_ACTIVITY_TIMEOUT = 240

ESPA_CHAR_SOH   = '\x01'
ESPA_CHAR_STX   = '\x02'
ESPA_CHAR_ETX   = '\x03'
ESPA_CHAR_ENQ   = '\x05'
ESPA_CHAR_ACK   = '\x06'
ESPA_CHAR_NAK   = '\x15'
ESPA_CHAR_EOT   = '\x04'
ESPA_CHAR_US    = '\x1F'
ESPA_CHAR_RS    = '\x1E'


class Notification(object):
    def __init__(self, title, data):
        self._title=title
        self._data=data

    @property
    def title(self):
        return self._title

    @property
    def data(self):
        return self._data

    def __getitem__(self, key):
        try:
            return self._data[key]
        except:
            pass

    def validate(self):
        return False


class NotificationCallToPager(Notification):
    def __init__(self, data):
        super(NotificationCallToPager, self).__init__('calltopager', data)

    @property
    def callAddress(self):
        return self['1']

    @property
    def message(self):
        return self['2']

    def validate(self):
        if self.callAddress and self.message:
            return True


class Link(object):
    def __init__(self):
        self._logger=None

    def setLogger(self, logger):
        self._logger=logger

    @property
    def logger(self):
        return self._logger

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


class LinkSerial(Link):
    def __init__(self, port, baudrate, parity=serial.PARITY_NONE, datasize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE):
        super(LinkSerial, self).__init__()
        self._serial=None
        self._port=port
        self._baudrate=baudrate
        self._parity=parity
        self._datasize=datasize
        self._stopbits=stopbits
        self._reopenTimeout=0

    def rtscts(self, enable=True):
        self._serial.rtscts=int(enable)

    def open(self):
        if self._serial:
            return True
        try:
            if time.time()>self._reopenTimeout:
                self._reopenTimeout=time.time()+15
                self.logger.info('open(%s)' % (self._port))

                s=serial.Serial(port=self._port,
                    baudrate=self._baudrate,
                    parity=self._parity,
                    stopbits=self._stopbits,
                    bytesize=self._datasize)

                s.timeout=0
                s.writeTimeout=0

                self._serial=s
                self.logger.info('port opened')

                return True
        except:
            self.logger.exception('open()')
            self._serial=None

    def close(self):
        try:
            self.logger.info('close()')
            #return self._serial.close()
        except:
            pass
        self._serial=None

    def read(self, size=255):
        try:
            if self.open():
                if size>0:
                    return bytearray(self._serial.read(size))
        except:
            self.logger.exception('read()')
            self.close()

    def write(self, data):
        try:
            if self.open():
                return self._serial.write(data)
        except:
            self.logger.exception('write()')
            self.close()


class Channel(object):
    def __init__(self, link, logger):
        self._logger=logger
        link.setLogger(logger)
        self._link=link
        self._activityTimeout=time.time()+ESPA_CLIENT_ACTIVITY_TIMEOUT
        self._inbuf=None
        self.reset()

    @property
    def logger(self):
        return self._logger

    def dataToString(self, data):
        try:
            return ':'.join('%02X' % b for b in data)
        except:
            return ''

    def reset(self):
        self.logger.info('reset()')
        self._link.reset()
        self._inbuf=bytearray()

    def open(self):
        return self._link.open()

    def close(self):
        return self._link.close()

    def receive(self, size=0):
        if time.time()>self._activityTimeout:
            self.logger.warning('client activity timeout !')
            self.close()
            self._activityTimeout=time.time()+60

        data=self._link.read()
        if data:
            self.logger.info('RX[%s]' % self.dataToString(data))
            self._inbuf.extend(data)
            self._activityTimeout=time.time()+ESPA_CLIENT_ACTIVITY_TIMEOUT

        try:
            if size>0:
                if len(self._inbuf)>=size:
                    data=self._inbuf[:size]
                    self._inbuf=self._inbuf[size:]
                    return data
            else:
                data=self._inbuf
                self._inbuf=bytearray()
            return data
        except:
            pass

    def receiveByte(self):
        return self.receive(1)

    # def waitByte(self, b):
    #     if b and b==self.receiveByte():
    #         return True

    def send(self, data):
        if data:
            if type(data)==type(''):
                data=bytearray(data)
            self.logger.info('TX[%s]' % self.dataToString(data))
            return self._link.write(data)

    def sendByte(self, b):
        self.send(bytearray(b))

    def ack(self):
        self.logger.debug('>ACK')
        self.sendByte(ESPA_CHAR_ACK)

    def eot(self):
        self.logger.debug('>EOT')
        self.sendByte(ESPA_CHAR_EOT)

    def nak(self):
        self.logger.debug('>NAK')
        self.sendByte(ESPA_CHAR_NAK)


class MessageServer(object):
    def __init__(self, channel, logger):
        self._logger=logger
        self._channel=channel
        self._state=0
        self._stateTimeout=0
        self._inbuf=None
        self._bcc=0

    @property
    def logger(self):
        return self._logger

    def setTimeout(self, timeout):
        if timeout is not None:
            self._stateTimeout=time.time()+timeout

    def setState(self, state, timeout=None):
        self._state=state
        self.logger.debug('setMessageState(%d)' % state)
        self.setTimeout(timeout)

    def setNextState(self, timeout=None):
        self.setState(self._state+1, timeout)

    def abort(self):
        self.setState(-1)

    def waitByte(self, b):
        if b:
            data=self._channel.receiveByte()
            if data:
                if b==data:
                    return True
                # reject stream incoherence
                self.abort()

    def manager(self):
        if self._state!=0 and time.time()>=self._stateTimeout:
            self.logger.warning('message state %d timeout!' % self._state)
            return False
        # --------------------------------------
        # reset
        if self._state==0:
            self.setNextState(3.0)
            self.logger.debug('WAITING FOR <SOH>')
        # --------------------------------------
        # wait for 'SOH'
        elif self._state==1:
            if self.waitByte(ESPA_CHAR_SOH):
                self._inbuf=bytearray()
                self._bcc=0
                self.setNextState(3.0)
                self.logger.debug('<SOH>OK, WAITING FOR BLOCK <DATA>+<ETX>')
        # --------------------------------------
        # wait for block <data>+<ETX>
        elif self._state==2:
            while True:
                b=self._channel.receiveByte()
                if not b:
                    break
                self._bcc ^= ord(b)
                if b==ESPA_CHAR_ETX:
                    self.logger.debug('<ETX>OK, WAITING FOR BCC')
                    self.setNextState()
                    break
                else:
                    self._inbuf.extend(b)
        # --------------------------------------
        # wait for 'BCC'
        elif self._state==3:
            b=self._channel.receiveByte()
            if b:
                if ord(b)==self._bcc:
                    self.logger.debug('<BCC>OK')
                    return self.decodeBuffer(self._inbuf)
                self.logger.error('<BCC>invalid')
                return False
        # --------------------------------------
        # bad state
        else:
            return False

    def decodeBuffer(self, buf):
        if buf:
            try:
                (header, body)=buf.split(ESPA_CHAR_STX)
                if header and body:
                    data={}
                    for record in body.split(ESPA_CHAR_RS):
                        if record:
                            (did, dvalue)=record.split(ESPA_CHAR_US)
                            data[str(did)]=str(dvalue)

                    notification=None
                    if header=='1':
                        notification=NotificationCallToPager(data)
                    else:
                        # '2'=Status Information,
                        # '3'=Status Request,
                        # '4'=Call subscriber line
                        self.logger.warning('unsupported function [%s]' % header)

                    if notification:
                        if notification.validate():
                            return notification
            except:
                self.logger.exception('decodeBuffer()')


class Server(object):
    def __init__(self, link, contolEquipmentAddress='1', pageingSystemAddress='2', logServer='localhost', logLevel=logging.DEBUG):
        logger=logging.getLogger("ESPASERVER")
        logger.setLevel(logLevel)
        socketHandler = logging.handlers.SocketHandler(logServer,
            logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        logger.addHandler(socketHandler)
        self._logger=logger

        self._controlEquipmentAddress=contolEquipmentAddress
        self._pageingSystemAddress=pageingSystemAddress

        self._channel=Channel(link, self._logger)
        self._eventStop=Event()
        self._state=0
        self._stateTimeout=0

        self._messageServer=None
        self.onInit()

    @property
    def logger(self):
        return self._logger

    def stop(self):
        if not self._eventStop.isSet():
            self._eventStop.set()

    def setTimeout(self, timeout):
        if timeout is not None:
            self._stateTimeout=time.time()+timeout

    def setState(self, state, timeout=None):
        self._state=state
        self.logger.debug('setServerState(%d)' % state)
        self.setTimeout(timeout)

    def setNextState(self, timeout=None):
        self.setState(self._state+1, timeout)

    def resetState(self):
        self._channel.eot()
        self.setState(0)

    def waitByte(self, b):
        if b:
            data=self._channel.receiveByte()
            if data:
                if b==data:
                    return True
                # reject stream incoherence
                self.resetState()

    def onInit(self):
        pass

    def manager(self):
        # ESPA state machine
        if self._state!=0 and time.time()>=self._stateTimeout:
            self.logger.warning('state %d timeout!' % self._state)
            self.resetState()

        # --------------------------------------
        # reset
        if self._state==0:
            self._channel.reset()
            self._messageServer=None
            self.setNextState(60)
            self.logger.debug('WAITING FOR <1>')
        # --------------------------------------
        # wait for '1'
        elif self._state==1:
            if self.waitByte(self._controlEquipmentAddress):
                # from here we let 2500ms to get the initial
                # '1' + ENQ + '2' + ENQ sequence
                self.setNextState(2.5)
                self.logger.debug('<1>OK, WAITING FOR <ENQ>')
        # --------------------------------------
        # wait for 'ENQ'
        elif self._state==2:
            if self.waitByte(ESPA_CHAR_ENQ):
                self.setNextState()
                self.logger.debug('<ENQ>OK, WAITING FOR <2>')
        # --------------------------------------
        # wait for '2'
        elif self._state==3:
            if self.waitByte(self._pageingSystemAddress):
                self.setNextState()
                self.logger.debug('<2>OK, WAITING FOR <ENQ>')
        # --------------------------------------
        # wait for 'ENQ'
        elif self._state==4:
            if self.waitByte(ESPA_CHAR_ENQ):
                self._channel.ack()
                self.setNextState(15.0)
                self.logger.debug('<ENQ>OK, WAITING FOR <MESSAGE>')
                self._messageServer=MessageServer(self._channel, self._logger)
        # --------------------------------------
        # manage espa message transaction
        elif self._state==5:
            if self._messageServer:
                notification=self._messageServer.manager()
                # Notification=completed, False=Failed, None=processing
                if notification:
                    self.onNotify(notification)
                    self._channel.ack()
                    self.resetState()
                elif notification is False:
                    self._channel.sendByte(self._controlEquipmentAddress)
                    self._channel.nak()
                    self.resetState()
        # --------------------------------------
        # bad state
        else:
            self.resetState()

    def onNotify(self, notification):
        return True

    def run(self):
        self._channel.open()

        while not self._eventStop.isSet():
            try:
                self.manager()
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()
            except:
                self.logger.exception('run()')
                self.stop()

        self._channel.close()


if __name__=='__main__':
    pass

