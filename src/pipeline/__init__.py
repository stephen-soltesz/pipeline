import socket

# third-party
import gflags

HOST = "localhost"
PORT = 3131

gflags.DEFINE_string("hostname", HOST,
    "Hostname of lineview server.", short_name='h')
gflags.DEFINE_integer("port", PORT,
    "TCP port to connect to hostname.", short_name='p')


class StreamSocket(object):
  """Wrap a socket with stream for client connections"""

  rbufsize = -1  # buffered
  wbufsize = 0  # unbuffered

  # A timeout to apply to the request socket, if not None.
  timeout = None  # disabled .. block indefinitely on read/write

  def __init__(self, hostname, port):
    ip_addr = socket.gethostbyname(hostname)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((ip_addr, port))

    if self.timeout is not None:
      self.sock.settimeout(self.timeout)

    self.rfile = self.sock.makefile('rb', self.rbufsize)
    self.wfile = self.sock.makefile('wb', self.wbufsize)

  def finish(self):
    """shutdown connection, flushing buffers and closing sockets."""
    if not self.wfile.closed:
      try:
        self.wfile.flush()
      except socket.error:
        # An final socket error may have occurred here, such as
        # the local error ECONNABORTED.
        pass
    self.wfile.close()
    self.rfile.close()
    self.sock.close()
