import logging
from SocketServer import BaseRequestHandler,ThreadingUDPServer,UDPServer
from tcp import TCP_Handler
from socket import socket, AF_INET, SOCK_DGRAM, timeout
import re
import sys

# DEBUG = False
PORT = 53
LOCAL_HOST = '127.0.0.1'
DNS_IF_MATCH = '' #'8.8.8.8'
DNS_IF_DOESNT_MATCH = '' #'10.10.0.21'
MULTITHREAD = True

if len(sys.argv) > 1:
	if sys.argv[1] == '-d':
		print 'debug mode on!'
		logging.basicConfig(level=logging.DEBUG)
else:
	logging.basicConfig(level=logging.INFO)
	# file_handler = logging.FileHandler('dns.log','a')
	# logging.root.addHandler(file_handler)
logger = logging.getLogger('dns')
re_program = []

def ReadSetting():
	global LOCAL_HOST
	global PORT
	global DNS_IF_MATCH
	global DNS_IF_DOESNT_MATCH
	try:
		s = open('setting','r')
		settings = s.readlines()
		for setting in settings:
			if setting[0] == '#':
				continue
			if setting.find('LOCAL_HOST') != -1:
				LOCAL_HOST = setting[setting.find('=')+1:].strip()
			elif setting.find('PORT') != -1:
				PORT = int(setting[setting.find('=')+1:].strip())
			elif setting.find('DNS_AUTHENTIC') != -1:
				DNS_IF_MATCH = setting[setting.find('=')+1:].strip()
			elif setting.find('DNS_INSECURITY') != -1:
				DNS_IF_DOESNT_MATCH = setting[setting.find('=')+1:].strip()
				
	except Exception, e:
		pass
		# s.close()

def WriteSetting():
	global LOCAL_HOST
	global PORT
	global DNS_IF_MATCH
	global DNS_IF_DOESNT_MATCH
	s = file('setting','w')
	content = 'LOCAL_HOST = %s\r\n' % LOCAL_HOST
	content += 'DNS_AUTHENTIC = %s\r\n' % DNS_IF_MATCH
	content += 'DNS_INSECURITY = %s\r\n' % DNS_IF_DOESNT_MATCH
	content += 'PORT = 53\r\n'
	s.write(content)
	s.close()
	
def ReadUrl():
	try:
		f = open('url','r')
		lines = f.readlines()
		for line in lines:
			line = line.strip()
			re_program.append(re.compile(line,re.I))
	except IOError, e:
		f = file('url','w')
		f.write('''google.com
facebook.com
google-analytics.com
googleapis.com
googlecode.com
googleusercontent.com
gstatic.com
goo.gl
t.co
twimg.com
wikipedia.org
ytimg.com
ggpht.com
twitter.com
fbcdn.net
blogspot.com
blogger.com
googlesyndication.com
googlevideo.com
youtube.com
''')
		f.close()
		ReadUrl()
	

def is_match(url):
	global re_program
	for program in re_program:
		if program.search(url):
			logging.info('url match![%s]',program.pattern)
			return program.pattern
	return None

class LocalDNSHandler(BaseRequestHandler,TCP_Handler):
	def setup(self):
		self.match_query = self.tcp_response
		self.no_match_query = self.get_response_normal
		self.normal_dns_server = (DNS_IF_DOESNT_MATCH,PORT)
		self.dnsserver = (DNS_IF_MATCH,PORT)
		self.tcp_dns_server = DNS_IF_MATCH
		self.port = PORT


	def handle(self):
		data, client_socket = self.request
		url = self.extract_url(data)
		if is_match(url):
			logging.info('match dns:[%s]',DNS_IF_MATCH)
			resp = self.match_query(data)
		else:
			logging.info("doesn't match dns:[%s]",DNS_IF_DOESNT_MATCH)
			resp = self.no_match_query(data)

		try:
			client_socket.sendto(resp,0,self.client_address)
		except StandardError as err:
			logger.error(err)

	def get_response_normal(self,data):
		logger.info('normal dns request')
		sock = socket(AF_INET, SOCK_DGRAM)
		sock.connect(self.normal_dns_server)
		sock.sendall(data)
		sock.settimeout(5)
		resp = ""
		try:
			resp = sock.recv(65535)
			logger.debug("normal dns reply:%s", resp.encode("hex"))
		except Exception as err:
			logger.error('%s ignored', err.message)
		sock.close()
		return resp


if MULTITHREAD:
	class LocalDNSServer(ThreadingUDPServer):
		pass
else:
	class LocalDNSServer(UDPServer):
		pass


def ReadDNS():
	global DNS_IF_DOESNT_MATCH
	import win32dns
	DNS_Servers = win32dns.RegistryResolve()
	if len(DNS_Servers):
		DNS_IF_DOESNT_MATCH = DNS_Servers[0]

def RunServer():
	global DNS_IF_MATCH
	global PORT
	global DNS_IF_DOESNT_MATCH
	global LOCAL_HOST

	ReadDNS()
	ReadSetting()
	
	if not DNS_IF_MATCH:
		d = raw_input('input Authentic DNS Server:')
		if d:
			DNS_IF_MATCH = d
		WriteSetting()

	ReadUrl()

	print 'LocalHost:',LOCAL_HOST
	print 'Port:',PORT
	print 'Dns_Authentic:',DNS_IF_MATCH
	print 'Dns_Insecurity:',DNS_IF_DOESNT_MATCH
	print '============================================'
	print 'Setup Local DNS Server to %s manually!' % LOCAL_HOST
	print '============================================'

	dnsserver = LocalDNSServer((LOCAL_HOST,PORT),LocalDNSHandler)
	dnsserver.serve_forever()

if __name__ == '__main__':
	RunServer()



