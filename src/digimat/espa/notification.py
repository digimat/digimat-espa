
class Notification(object):
    def __init__(self, source, name, data=None):
        self._source=source
        self._name=name
        self._data=data
        self.buildFromData(data)

    def buildFromData(self, data):
        pass

    @property
    def source(self):
        return self._source

    @property
    def name(self):
        return self._name

    def isName(self, name):
        if name and name.lower()==self.name.lower():
            return True

    @property
    def data(self):
        return self._data

    def __getitem__(self, key):
        try:
            return self._data[key]
        except:
            pass

    def validate(self):
        return True

    def __repr__(self):
        return '%s:%s' % (self.source, self.name)


class NotificationCallToPager(Notification):
    def __init__(self, source, data):
        self._message=None
        self._callAddress=None
        self._beepCoding=None
        self._callType=None
        self._priority=None
        super(NotificationCallToPager, self).__init__(source, 'calltopager', data)

    def buildFromData(self, data):
        # http://www.gscott.co.uk/ESPA.4.4.4/datablock.html

        try:
            self._message=self.espaCharsetToUTF8(data['1'])
        except:
            pass

        try:
            self._callAddress=data['2']
        except:
            pass

        try:
            self._beepCoding=data['3']
        except:
            pass

        try:
            self._callType=data['4']
        except:
            pass

        try:
            self._priority=data['6']
        except:
            pass

    def espaCharsetToUTF8(self, message):
        # todo
        return message

    @property
    def callAddress(self):
        return self._callAddress

    @property
    def message(self):
        return self._message

    def validate(self):
        if self.callAddress and self.message:
            return True

    def __repr__(self):
        return '%s:%s(%s,%s)' % (self.source, self.name, self.callAddress, self.message)


class NotificationLinkTimeout(Notification):
    def __init__(self, source):
        super(NotificationLinkTimeout, self).__init__(source, 'linktimeout')


if __name__=='__main__':
    pass
