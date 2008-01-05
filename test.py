import unittest
from mod_jabber import parse_xmpp_uri, normalize_xmpp_uri

class TestNormalizeXmppUri(unittest.TestCase):
	def testNormalizeTraditionalFormWithStructuredResource(self):
		self.assertEqual("node:****@host.com/resource/subresource", normalize_xmpp_uri("node@host.com/resource/subresource:****"))

	def testNormalizeTraditionalFormWithResource(self):
		self.assertEqual("node:****@host.com/resource", normalize_xmpp_uri("node@host.com/resource:****"))

	def testNormalizeTraditionalForm(self):
		self.assertEqual("node:****@host.com", normalize_xmpp_uri("node@host.com:****"))

	def testNormalizeModernFormWithStructuredResource(self):
		self.assertEqual("node:****@host.com/resource/subresource", normalize_xmpp_uri("node:****@host.com/resource/subresource"))

	def testNormalizeModernFormWithResource(self):
		self.assertEqual("node:****@host.com/resource", normalize_xmpp_uri("node:****@host.com/resource"))

	def testNormalizeModernForm(self):
		self.assertEqual("node:****@host.com", normalize_xmpp_uri("node:****@host.com"))

class TestParseXmppUri(unittest.TestCase):
	def testParseUriWithoutResource(self):
		self.assertEqual({"node": "user", "password": "****", "host": "host.com", "resource": ""}, parse_xmpp_uri("user:****@host.com"))
	
	def testParseUriWithResource(self):
		self.assertEqual({"node": "user", "password": "****", "host": "host.com", "resource": "res"}, parse_xmpp_uri("user:****@host.com/res"))


if __name__ == '__main__':
	unittest.main()
