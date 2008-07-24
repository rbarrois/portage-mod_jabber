# -*- coding: utf-8 -*-
#
# portage-mod_jabber - An XMPP plugin for Gentoo Portage
#
# Copyright © 2005 - 2008 Lars Strojny <lars@strojny.net>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

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
	parts = matched.groupdict ()
	parts['resource'] = \
		parts['resource'] \
			.replace ('%hostname%', socket.gethostname ()) \
			.replace ('%HOSTNAME%', socket.gethostname ()) \
			.replace ('${hostname}', socket.gethostname ()) \
			.replace ('${HOSTNAME}', socket.gethostname ())
	return parts

def xmpp_client_factory (sender):
	try:
		client = xmpp.Client (sender["host"], debug = False)
		connected = client.connect ()
		if not connected:
			raise PortageException \
				("!!! Unable to connect to %s" % sender['server'])
		if connected <> 'tls':
			raise PortageException ("!!! Warning: unable to estabilish secure connection - TLS failed!")
		auth = client.auth (sender['node'], sender['password'], sender['resource'])
		if not auth:
			raise PortageException \
				("!!! Could not authentificate to %s" % sender['server'])
		if auth <> 'sasl':
			raise PortageException \
				("!!! Unable to perform SASL auth to %s" % sender['server'])
		return client
	except Exception, e:
		raise PortageException \
			("!!! An error occured while connecting to jabber server %s" % str (e))

def send_xmpp_message (client, recipient, subject, text):
	try:
		message = xmpp.protocol.Message (recipient, text, "message", subject)
		client.send (message)
	except Exception, e:
		raise PortageException \
			("!!! An error occured while sending a jabber message to %s: %s" \
				% recipient, str (e))

def process (settings, package, logentries, fulltext):
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
		subject = subject.replace ("${PACKAGE}", package)
		subject = subject.replace ("${HOST}", socket.getfqdn())
		sender = settings["PORTAGE_ELOG_JABBERFROM"]
		if not ":" in sender or not "@" in sender:
			raise PortageException("!!! Invalid syntax for PORTAGE_ELOG_JABBERFROM. Use user:password@host[/resource]")
		sender = normalize_xmpp_uri (settings["PORTAGE_ELOG_JABBERFROM"])
		sender  = parse_xmpp_uri (sender)
		client = xmpp_client_factory (sender)
		for recipient in settings["PORTAGE_ELOG_JABBERTO"].split(" "):
			send_xmpp_message (client, recipient, subject, fulltext)

