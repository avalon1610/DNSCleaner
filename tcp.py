import struct
import socket
import Queue
import logging

logger = logging.getLogger('tcp')
TIMEOUT = 0.4

tcp_pool = Queue.Queue()
class TCP_Handler(object):
	def extract_url(self,data):
		logging.debug("raw dns request: %s",data.encode('hex'))
		data = data[12:]
		url = []
		start = 0
		len_of_data = ord(data[start])
		logging.debug("len_of_data: %s",len_of_data)
		while len_of_data != 0:
			part = str(data[start+1:start+1+len_of_data])
			logging.debug('part:%s',part)
			url.append(part)
			start = start+len_of_data+1
			len_of_data = ord(data[start])
		url = '.'.join(url)
		logging.info('requesting url:%s',url)
		return url

	def tcp_response(self,data):
		resp = None
		while not resp:
			sock = self.get_tcp_sock()
			size_data = self.tcp_packet_head(data)
			sock.send(size_data + data)
			try:
				resp = sock.recv(1024)
				logging.debug('receive data: %s',resp.encode('hex'))
			except socket.timeout:
				logging.debug('tcp socket timeout,abandon')
				sock = self.create_tcp_sock()
		
		self.release_tcp_sock(sock)
		return self.packet_body(resp)

	def release_tcp_sock(self,sock):
		try:
			tcp_pool.put(sock,block=False)
		except Queue.Full:
			logger.debug("tcp pool is full,abandon oldest socket")
			old_sock = tcp_pool.get(block=False)
			old_sock.close()
			tcp_pool.put(sock,block=False)

	def packet_body(self,data):
		size = struct.unpack('!H',data[0:2])[0]
		logging.debug('response package size: %d',size)
		logging.debug('len of response: %d',len(data))
		return data[2:2+size]

	def tcp_packet_head(self,data):
		size = len(data)
		size_data = struct.pack('!H',size)
		logging.debug('head data len: %d',size)
		logging.debug('head data: %s',size_data.encode('hex'))
		return size_data

	def get_tcp_sock(self):
		try:
			sock = tcp_pool.get(block=True,timeout=TIMEOUT)
		except Queue.Empty:
			logging.debug('tcp pool is empty,create a new socket')
			sock = self.create_tcp_sock()
		return sock

	def create_tcp_sock(self):
		# tcp_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		# tcp_sock.connect((self.tcp_dns_server,self.port))
		# tcp_sock.settimeout(5)
		# return tcp_sock

		s = None
		for res in socket.getaddrinfo(self.tcp_dns_server,self.port,socket.AF_UNSPEC,socket.SOCK_STREAM):
			af,socktype,proto,canonname,sa = res
			try:
				s = socket.socket(af,socktype,proto)
			except socket.error as msg:
				s = None
				continue

			try:
				s.connect(sa)
			except socket.error as msg:
				s.close()
				s = None
				continue

		if s is None:
			logging.error('could not open socket to %s',self.tcp_dns_server)
		else:
			s.settimeout(5)
			return s