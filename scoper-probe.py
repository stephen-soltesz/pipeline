#!/usr/bin/env python

import os
import socket
import sys
import time
import logging

try:
  import gflags
  FLAGS = gflags.FLAGS
except Exception as e:
  print "Failed to 'import gflags'"
  print "Try installing python-gflags package"
  sys.exit(1)


gflags.DEFINE_string("hostname", None, "Hostname of scoper server.", short_name='h')
gflags.DEFINE_integer("port", 3131, "TCP port to connect to hostname.", short_name='p')
gflags.DEFINE_string("label", None, "Send specific label to scoper for this line", short_name='l')
gflags.DEFINE_string("color", None, "Send specific color to scoper for this line", short_name='C')
gflags.DEFINE_string("style", None, "Send specific style hints to scoper", short_name='s')
gflags.DEFINE_string("command", None, 
                     ("Rather than read from stdin, "
                      "use output from given command."),
                     short_name='c')
gflags.DEFINE_float("interval", 1, "Delay in milliseconds between running command.",
    lower_bound=0.0, short_name='i')

class StreamSocket(object):
  """Wrap a socket with stream for client connections"""

  # Default buffer sizes for rfile, wfile.
  # We default rfile to buffered because otherwise it could be
  # really slow for large data (a getc() call per byte); we make
  # wfile unbuffered because (a) often after a write() we want to
  # read and we need to flush the line; (b) big writes to unbuffered
  # files are typically optimized by stdio even when big reads
  # aren't.
  rbufsize = -1
  wbufsize = 0

  # A timeout to apply to the request socket, if not None.
  timeout = None

  # Disable nagle algorithm for this socket, if True.
  # Use only when wbufsize != 0, to avoid small packets.
  disable_nagle_algorithm = False

  def __init__(self, hostname, port):
    ip = socket.gethostbyname(hostname)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((ip, port))

    if self.timeout is not None:
      self.sock.settimeout(self.timeout)
    if self.disable_nagle_algorithm:
      self.sock.setsockopt(socket.IPPROTO_TCP,
                           socket.TCP_NODELAY, True)

    self.rfile = self.sock.makefile('rb', self.rbufsize)
    self.wfile = self.sock.makefile('wb', self.wbufsize)

  def finish(self):
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

def usage():
  return "TODO: add usage()"

def parse_args():
    try:
        FLAGS(sys.argv)
    except gflags.FlagsError, err:
        print usage()
        print '%s\nUsage: %s ARGS\n%s' % (err, sys.argv[0], FLAGS)
        sys.exit(1)

    if len(sys.argv) == 1:
        print usage()
        print 'Usage: %s ARGS\n%s' % (sys.argv[0], FLAGS)
        sys.exit(1)

    logging.basicConfig(format = '[%(asctime)s] %(levelname)s: %(message)s',
                        level = logging.INFO)


def main():
  parse_args()

  client = StreamSocket(FLAGS.hostname, FLAGS.port)
  if FLAGS.color:
    client.wfile.write("color:%s\n" % FLAGS.color)
  if FLAGS.label:
    client.wfile.write("label:%s\n" % FLAGS.label)
  if FLAGS.style:
    client.wfile.write("%s\n" % FLAGS.style.replace(',', '\n'))
  client.wfile.write("BEGIN\n")

  while True:
    if FLAGS.command:
      value = os.popen(FLAGS.command, 'r').read()
      client.wfile.write(value)
      logging.info("Send to %s:%s '%s'" % (FLAGS.hostname,
                   FLAGS.port, value.strip()))
      # wait before re-running command
      time.sleep(FLAGS.interval)
    else:
      # just read from stdin
      line = sys.stdin.readline()
      if line == "": break
      # do not sleep, read as quickly as possible
      client.wfile.write(line)

if __name__ == "__main__":
  main()
