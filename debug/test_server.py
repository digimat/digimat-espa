import time
from digimat.espa import Server, LinkSerial

link=LinkSerial('alarming', 'COM5', 9600, 'N', 8, 1)
server=Server(link)

server.start()

while server.isRunning():
	try:
		notification=server.getNotification()
		if notification:
			print notification
			if notification.isName('calltopager'):
				print "--> paging(%s) with message <%s>..." % (notification.callAddress, notification.message)

		time.sleep(0.2)
	except:
		server.stop()

server.waitForExit()