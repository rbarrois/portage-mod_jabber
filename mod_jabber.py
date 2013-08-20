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

import sleekxmpp


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


class ElogClient(sleekxmpp.ClientXMPP):
    """Handles elog messages."""
    def __init__(self, jid, password, handler):
        super(ElogClient, self).__init__(jid, password)
        self.on_connect_handler = handler
        self.add_event_handler('session_start', self.on_connect, threaded=True)

    def on_connect(self, event):
        self.on_connect_handler.handle(self, event)


class ElogHandler(object):
    def __init__(self, message):
        self.message = message

    def handle(self, client, event):
        """Process the 'connected' event."""
        client.send_presence()
        client.get_roster()

        for target in self.message['targets']:
            client.send_message(
                mto=target,
                msubject=self.message['subject'],
                mbody=self.message['message'],
            )
        client.disconnect(wait=True)


class ElogProcessor(object):
    """Processes Elog messages."""

    def __init__(self, sender, portage_settings):
        self.sender = self.parse_uri(sender)
        self.portage_settings = portage_settings

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

    def prepare_message(self, package, fulltext):
        """Prepare the message to send."""
        pattern = (self.portage_settings['PORTAGE_ELOG_JABBERSUBJECT']
                or self.portage_settings['PORTAGE_ELOG_MAILSUBJECT'])

        host = socket.getfqdn()
        subject = (pattern
            .replace('${PACKAGE}', package)
            .replace('${HOST}', host)
        )
        return {
            'subject': subject,
            'message': fulltext,
            'targets': self.portage_settings['PORTAGE_ELOG_JABBERTO'].split(),
          }

    # XMPP backend-specific methods
    @classmethod
    def make_jid(cls, sender):
        """Parse our 'sender' JID"""
        resource = cls.interpolate_resource(sender['resource'])
        return sleekxmpp.JID(
            local=sender['node'],
            domain=sender['host'],
            resource=resource,
        )

    def make_client(self, connected_handler):
        """Prepare a XMPP client.

        Adds a 'connected' handler."""
        jid = self.make_jid(self.sender)
        return ElogClient(jid, self.sender['password'], handler=connected_handler)

    def make_handler(self, message):
        """Prepare the 'connected' handler."""
        return ElogHandler(message)

    def notify(self, package, fulltext):
        message = self.prepare_message(package, fulltext)
        handler = self.make_handler(message)
        client = self.make_client(handler)
        if client.connect():
            client.process(block=True)


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
