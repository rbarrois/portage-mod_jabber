import socket, xmpp, re
from urlparse import urlparse, urlsplit
try:
	from portage.exception import PortageException
except ImportError:
	# Portage <2.2 compatibility
	from portage_exception import PortageException


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
def parse_xmpp_uri (uri):
	regex = re.compile ("^(?P<node>[^:]+):(?P<password>[^@]+)@(?P<host>[^/]+)/?(?P<resource>.*)")
	matched = regex.match (uri)
	return matched.groupdict ()

def process (settings, cpv, logentries, fulltext):
	# Syntax for PORTAGE_ELOG_JABBERFROM:
	# jid [user:password@host[/resource]
	# where jid:       sender jabber id
	#       user:      jabber user
	#       server:    jabber server
	#       password:  password to authentificate
	#
	# Syntax for PORTAGE_ELOG_JABBERTO:
	# jid user@host[ user@host]
	# where jid: one or more jabber id separated by a whitespace
	if settings["PORTAGE_ELOG_JABBERFROM"]:
		subject = settings["PORTAGE_ELOG_JABBERSUBJECT"]
		if not subject:
			subject = settings["PORTAGE_ELOG_MAILSUBJECT"]
		subject = subject.replace("${PACKAGE}", cpv)
		subject = subject.replace("${HOST}", socket.getfqdn())
		sender = settings["PORTAGE_ELOG_JABBERFROM"]
		if not ":" in sender or not "@" in sender:
			raise PortageException("!!! Invalid syntax for PORTAGE_ELOG_JABBERFROM. Use user:password@host[/resource]")
		sender  = normalize_xmpp_uri (settings["PORTAGE_ELOG_JABBERFROM"])
		parts   = parse_xmpp_uri (sender)
		for recipient in settings["PORTAGE_ELOG_JABBERTO"].split(" "):
			try:
				client = xmpp.Client (parts["host"], debug = False)
				connected = client.connect ()
				if not connected:
					raise PortageException ("!!! Unable to connect to %s" %server)
				if connected <> 'tls':
					raise PortageException ("!!! Warning: unable to estabilish secure connection - TLS failed!")

				auth = client.auth (parts['node'], parts['password'], parts['resource'])
				if not auth:
					raise PortageException ("!!! Could not authentificate to %s" %server)
				if auth <> 'sasl':
					raise PortageException ("!!! Unable to perform SASL auth to %s" %server)
				message = xmpp.protocol.Message (recipient, fulltext, "message", subject)

				client.send (message)
			except Exception, e:
				raise PortageException ("!!! An error occured while sending a jabber message to "+str(recipient)+": "+str(e))
