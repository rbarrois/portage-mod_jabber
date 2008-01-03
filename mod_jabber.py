import socket, portage_exception, xmpp

def process(mysettings, cpv, logentries, fulltext):
	# Syntax for PORTAGE_ELOG_JABBERFROM:
	# jid [user@host:password]
	# where jid:       sender jabber id
	#       user:      jabber user
	#       server:    jabber server
	#       password:  password to authentificate
	#
	# Syntax for PORTAGE_ELOG_JABBERTO:
	# jid user@host[ user@host]
	# where jid: one or more jabber id separated by a whitespace
	if mysettings["PORTAGE_ELOG_JABBERFROM"]:
		if not ":" in mysettings["PORTAGE_ELOG_JABBERFROM"]:
			raise portage_exception.PortageException("!!! Invalid syntax for PORTAGE_ELOG_JABBERFROM. Use user@host[/resource]:password")
		myfrom, mypass = mysettings["PORTAGE_ELOG_JABBERFROM"].split(":")
		mysubject = mysettings["PORTAGE_ELOG_JABBERSUBJECT"]
		if not mysubject:
			mysubject = mysettings["PORTAGE_ELOG_MAILSUBJECT"]
		mysubject = mysubject.replace("${PACKAGE}", cpv)
		mysubject = mysubject.replace("${HOST}", socket.getfqdn())
		mytos = mysettings["PORTAGE_ELOG_JABBERTO"].split(" ")
		for myto in mytos:
			jid = xmpp.JID(myfrom)
			myuser, myserver, myresource = jid.getNode(), jid.getDomain(), jid.getResource().replace("%hostname%", socket.gethostname())
			try:
				client = xmpp.Client(myserver, debug = False)
				connected = client.connect()
				if not connected:
					raise portage_exception.PortageException("!!! Unable to connect to %s" %myserver)
				if connected <> 'tls':
					raise portage_exception.PortageException("!!! Warning: unable to estabilish secure connection - TLS failed!")

				auth = client.auth(myuser,mypass, myresource)
				if not auth:
					raise portage_exception.PortageException("!!! Could not authentificate to %s" %myserver)
				if auth <> 'sasl':
					raise portage_exception.PortageException("!!! Unable to perform SASL auth to %s" %myserver)
				mymessage = xmpp.protocol.Message(myto, fulltext, "message", mysubject)

				client.send(mymessage)
			except Exception, e:
				raise portage_exception.PortageException("!!! An error occured while sending a jabber message to "+str(myto)+": "+str(e))
