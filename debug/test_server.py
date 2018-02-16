from digimat.espa import LinkSerial, Server, MultiChannelServer


class MyMultiChannelServer(MultiChannelServer):
    def onNotification(self, notification):
        print( notification )
        if notification.isName('calltopager'):
            print( "[%s]->paging(%s, %s)" % (notification.source,
                 notification.callAddress,
                 notification.message) )


servers=MyMultiChannelServer()

link=LinkSerial('ts940', 'COM1', 9600, 'N', 8, 1)
servers.add(Server(link))

link=LinkSerial('espa2', 'COM2', 9600, 'N', 8, 1)
servers.add(Server(link))

servers.run()
