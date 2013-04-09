# -*- coding: utf-8 -*-
#
# portage-mod_jabber - An XMPP plugin for Gentoo Portage
#
# Copyright © 2005-2008 Lars Strojny <lars@strojny.net>
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

import socket
import re

from pyxmpp2.client import Client
from pyxmpp2.interfaces import EventHandler, event_handler, QUIT
from pyxmpp2.jid import JID
from pyxmpp2.message import Message
from pyxmpp2.settings import XMPPSettings
from pyxmpp2.streamevents import AuthorizedEvent, DisconnectedEvent


try:
    from portage.exception import PortageException
except ImportError:
    # Portage <2.2 compatibility
    try:
        from portage_exception import PortageException
    except ImportError:
        # No portage installed
        class PortageException(Exception):
            pass


class ElogHandler(EventHandler):
    """Handles elog messages."""
    def __init__(self, targets, subject, fulltext):
        self.targets = targets
        self.subject = subject
        self.fulltext = fulltext

    @event_handler(AuthorizedEvent)
    def handle_authorized(self, event):
        """Just received authorization."""
        for target in self.targets:
            message = Message(to_jid=target, subject=self.subject, body=self.fulltext)
            event.stream.send(message)
        event.stream.disconnect()

    @event_handler(DisconnectedEvent)
    def handle_disconnected(self, event):
        return QUIT

    @event_handler()
    def handle_all(self, event):
        pass


class ElogProcessor(object):
    """Processes Elog messages."""

    def __init__(self, sender, settings):
        self.sender = self._parse_uri(sender)
        self.settings = settings

    @classmethod
    def parse_uri(cls, uri):
        # For user:password@host/resource
        base_regex = r'^(?P<node>[^:@]+):(?P<password>[^@]+)@(?P<host>[^/]+)(?:/(?P<resource>.*))?$'
        # For user@host/resource:password
        alt_regex = r'^(?P<node>[^@]+)@(?P<host>[^/:]+)(?:/(?P<resource>[^:]+))?:(?P<password>.*)$'

        base_match = re.match(base_regex, uri)
        if base_match:
            return base_match.groupdict()

        alt_match = re.match(alt_regex, uri)
        if alt_match:
            return alt_match.groupdict()

        raise PortageException("No suitable URI found in %s" % uri)

    @classmethod
    def interpolate_resource(cls, resource):
        if not resource:
            return ''
        hostname = socket.gethostname()
        return (resource
            .replace('%hostname%', hostname)
            .replace('%HOSTNAME%', hostname)
            .replace('${hostname}', hostname)
            .replace('${HOSTNAME}', hostname)
        )

    @classmethod
    def make_jid(cls, sender):
        resource = cls.interpolate_resource(sender['resource'])
        return JID(
            local_or_jid=sender['node'],
            domain=sender['host'],
            resource=resource,
        )

    @classmethod
    def make_settings(cls, sender):
        settings = XMPPSettings({
            'starttls': True,
            'tls_verify_peer': False,
        })
        if sender['password']:
            settings['password'] = sender['password']
        return settings

    def make_client(self, handler):
        """Prepare a XMPP client."""
        jid = self.make_jid(self.sender)
        return Client(jid, [handler], settings)

    @classmethod
    def make_subject(cls, pattern, package):
        host = socket.getfqdn()
        return (pattern
            .replace('${PACKAGE}', package)
            .replace('${HOST}', host)
        )

    def make_handler(self, package, fulltext):
        pattern = self.settings['PORTAGE_ELOG_JABBERSUBJECT'] or self.settings['PORTAGE_ELOG_MAILSUBJECT']
        subject = self.make_subject(pattern, package)
        return ElogHandler(
            targets=self.settings['PORTAGE_ELOG_JABBERTO'].split(),
            subject=subject,
            fulltext=fulltext,
        )

    def notify(self, package, fulltext):
        handler = self.make_handler(package, fulltext)
        client = self.make_client(handler)
        client.connect()
        client.run()


def process(settings, package, logentries, fulltext):
    """Portage plugin hook

        Configuration:
        Syntax for PORTAGE_ELOG_JABBERFROM:
            jid [user:password@host[/resource]
            where jid: sender jabber id
               user:      jabber user
               server:    jabber server
               password:  password to authentificate
               resource:  sender resource which might include placeholders

        Syntax for PORTAGE_ELOG_JABBERTO:
            jid user@host[ user@host]
            where jid: one or more jabber id separated by a whitespace
    """
    sender = settings['PORTAGE_ELOG_JABBERFROM']
    if not sender:
        return

    processor = ElogProcessor(sender, settings)
    processor.notify(package, fulltext)
