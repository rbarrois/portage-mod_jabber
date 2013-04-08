
import socket
import unittest

from mod_jabber import ElogProcessor

class TestNormalizeXmppUri(unittest.TestCase):
    def testNormalizeTraditionalFormWithStructuredResource(self):
        parsed = ElogProcessor.parse_uri('node@host.com/resource/subresource:****')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': 'resource/subresource',
            'password': '****',
        }, parsed)

    def testNormalizeTraditionalFormWithResource(self):
        parsed = ElogProcessor.parse_uri('node@host.com/resource:****')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': 'resource',
            'password': '****',
        }, parsed)

    def testNormalizeTraditionalForm(self):
        parsed = ElogProcessor.parse_uri('node@host.com:****')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': None,
            'password': '****',
        }, parsed)

    def testNormalizeModernFormWithStructuredResource(self):
        parsed = ElogProcessor.parse_uri('node:****@host.com/resource/subresource')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': 'resource/subresource',
            'password': '****',
        }, parsed)

    def testNormalizeModernFormWithResource(self):
        parsed = ElogProcessor.parse_uri('node:****@host.com/resource')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': 'resource',
            'password': '****',
        }, parsed)

    def testNormalizeModernForm(self):
        parsed = ElogProcessor.parse_uri('node:****@host.com')

        self.assertEqual({
            'node': 'node',
            'host': 'host.com',
            'resource': None,
            'password': '****',
        }, parsed)


class InterpolateResourceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = socket.gethostname()

    def test_interpolate_no_hostname(self):
        res = ElogProcessor.interpolate_resource('foo/bar/baz')
        self.assertEqual('foo/bar/baz', res)

    def test_interpolate_upper_percent(self):
        res = ElogProcessor.interpolate_resource('foo/%HOSTNAME%/bar')
        self.assertEqual('foo/%s/bar' % self.host, res)

    def test_interpolate_lower_percent(self):
        res = ElogProcessor.interpolate_resource('foo/%hostname%/bar')
        self.assertEqual('foo/%s/bar' % self.host, res)

    def test_interpolate_lower_dollar(self):
        res = ElogProcessor.interpolate_resource('foo/${hostname}/bar')
        self.assertEqual('foo/%s/bar' % self.host, res)

    def test_interpolate_upper_dollar(self):
        res = ElogProcessor.interpolate_resource('foo/${HOSTNAME}/bar')
        self.assertEqual('foo/%s/bar' % self.host, res)

    def test_interpolate_lower_percent(self):
        res = ElogProcessor.interpolate_resource('foo/%hostname%/bar')
        self.assertEqual('foo/%s/bar' % self.host, res)


class MakeJIDTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = socket.gethostname()

    def test_no_resource(self):
        jid = ElogProcessor.make_jid(ElogProcessor.parse_uri('node:****@host.com'))
        self.assertEqual('node', jid.local)
        self.assertEqual('host.com', jid.domain)
        self.assertEqual(None, jid.resource)

    def test_simple_resource(self):
        jid = ElogProcessor.make_jid(ElogProcessor.parse_uri('node:****@host.com/foo'))
        self.assertEqual('node', jid.local)
        self.assertEqual('host.com', jid.domain)
        self.assertEqual('foo', jid.resource)

    def test_hostname_resource(self):
        jid = ElogProcessor.make_jid(ElogProcessor.parse_uri('node:****@host.com/foo/%hostname%'))
        self.assertEqual('node', jid.local)
        self.assertEqual('host.com', jid.domain)
        self.assertEqual('foo/%s' % self.host, jid.resource)


class MakeSettingsTestCase(unittest.TestCase):

    def test_no_resource(self):
        settings = ElogProcessor.make_settings(ElogProcessor.parse_uri('node:****@host.com'))
        self.assertTrue(settings['starttls'])
        self.assertFalse(settings['tls_verify_peer'])
        self.assertEqual('****', settings['password'])

    def test_simple_resource(self):
        settings = ElogProcessor.make_settings(ElogProcessor.parse_uri('node:****@host.com/foo'))
        self.assertTrue(settings['starttls'])
        self.assertFalse(settings['tls_verify_peer'])
        self.assertEqual('****', settings['password'])

    def test_hostname_resource(self):
        settings = ElogProcessor.make_settings(ElogProcessor.parse_uri('node:****@host.com/foo/%hostname%'))
        self.assertTrue(settings['starttls'])
        self.assertFalse(settings['tls_verify_peer'])
        self.assertEqual('****', settings['password'])


class MakeSubjectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = socket.getfqdn()

    def test_fixed(self):
        subject = ElogProcessor.make_subject('foo-bar', 'app-misc/foo')
        self.assertEqual('foo-bar', subject)

    def test_package(self):
        subject = ElogProcessor.make_subject('[${PACKAGE}] elog', 'app-misc/foo')
        self.assertEqual('[app-misc/foo] elog', subject)

    def test_host(self):
        subject = ElogProcessor.make_subject('[${HOST}] elog', 'app-misc/foo')
        self.assertEqual('[%s] elog' % self.host, subject)

    def test_host_package(self):
        subject = ElogProcessor.make_subject('[${PACKAGE}] elog on ${HOST}', 'app-misc/foo')
        self.assertEqual('[app-misc/foo] elog on %s' % self.host, subject)



if __name__ == '__main__':
    unittest.main()
