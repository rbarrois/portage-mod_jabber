import socket, portage_exception, xmpp, re
from urlparse import urlparse, urlsplit

"""
	user:pw@host.com[/resource]
	user@host.com[/resource]:pw

	=> user:pw@host.com[/resource]
"""
def normalize_xmpp_uri(uri):
	if uri.find("@") < uri.find(":"):
		uri = uri.replace("@", ":" + uri.partition(":")[2] + "@").rpartition(":")[0]
	return uri

"""
	user:pw@host.com[/resource]
	=> {
		node: <user>
		password: <pw>
		host: <host>
		resource: <resource>
	}
"""
def parse_xmpp_uri(uri):
	regex = re.compile("^(?P<node>[^:]+):(?P<password>[^@]+)@(?P<host>[^/]+)/?(?P<resource>.*)")
	matched = regex.match(uri)
	return matched.groupdict()

def process(settings, cpv, logentries, fulltext):
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
	if settings["PORTAGE_ELOG_JABBERFROM"]:
		if not ":" in settings["PORTAGE_ELOG_JABBERFROM"]:
			raise portage_exception.PortageException("!!! Invalid syntax for PORTAGE_ELOG_JABBERFROM. Use user@host[/resource]:password")
		sender, password = settings["PORTAGE_ELOG_JABBERFROM"].split(":")
		subject = settings["PORTAGE_ELOG_JABBERSUBJECT"]
		if not subject:
			subject = settings["PORTAGE_ELOG_MAILSUBJECT"]
		subject = subject.replace("${PACKAGE}", cpv)
		subject = subject.replace("${HOST}", socket.getfqdn())
		for recipient in settings["PORTAGE_ELOG_JABBERTO"].split(" "):
			sender = normalize_xmpp_uri (sender)
			parts = parse_xmpp_uri (sender)
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
				mymessage = xmpp.protocol.Message(recipient, fulltext, "message", mysubject)

				client.send(mymessage)
			except Exception, e:
				raise portage_exception.PortageException("!!! An error occured while sending a jabber message to "+str(recipient)+": "+str(e))
