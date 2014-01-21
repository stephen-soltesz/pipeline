#!/usr/bin/env python

import errno
import os
import socket
import sys
import time
import logging

try:
  import gflags
  FLAGS = gflags.FLAGS
except ImportError as error:
  print "Failed to 'import gflags'"
  print "Try installing python-gflags package"
  sys.exit(1)


gflags.DEFINE_string("hostname", None, "Hostname of scoper server.", short_name='h')
gflags.DEFINE_integer("port", 3131, "TCP port to connect to hostname.", short_name='p')
gflags.DEFINE_string("label", None, "Send specific label to scoper for this line", short_name='l')
gflags.DEFINE_string("axis", "default", "Use a specific axis name.", short_name='a')
gflags.DEFINE_string("axis_ylabel", "Value", "Use a specific axis name.", short_name='y')
gflags.DEFINE_string("axis_xlabel", "Samples", "Use a specific axis name.", short_name='x')
gflags.DEFINE_string("color", None, "Send specific color to scoper for this line", short_name='C')
gflags.DEFINE_string("style", None, "Send specific style hints to scoper", short_name='s')
gflags.DEFINE_string("command", None,
                     ("Rather than read from stdin, "
                      "use output from given command."),
                     short_name='c')

# TODO: need some insight into graph move of timestamps or samples...
gflags.DEFINE_integer("pivot", None,
    ("Wrap all lines around given pivot point. Use with '--width' to create "
     "a fixed size window for comparing new graphs with long-running graphs."),
    short_name='P')
gflags.DEFINE_bool("reset", False, "Send 'RESET' command to grapher.", short_name='r')
gflags.DEFINE_float("interval", 1, "Delay in milliseconds between running command.",
    lower_bound=0.0, short_name='i')
gflags.MarkFlagAsRequired('hostname')


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
  return """
Summary:

  scoper-probe.py connects to the scoper-graph server and sends values to the
  server for plotting.  The new values are either read from stdin, or returned
  by a command executed by scoper-probe.

Examples:
  Start the scoper-graph.py server, then try one of the following.

  Read new values from STDIN - plots a sin() wave using bc:
  for i in {0..200}; do \\
      echo "s($i/(4*3.14))" | bc -l ; done \\
  | scoper-probe.py -h localhost

  Read new values from command every 5 seconds:
  scoper-probe.py -h localhost  --command "echo 's({i}/(3.14*4))' | bc -l"
  """

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


def connect_to_grapher():
  try:
    client = StreamSocket(FLAGS.hostname, FLAGS.port)
  except socket.error as error:
    print error
    if error.errno == errno.ECONNREFUSED:
      print "Is the server running at (%s,%s)?" % (FLAGS.hostname, FLAGS.port)
    sys.exit(1)

  if FLAGS.reset:
    client.wfile.write("RESET\n")
    sys.exit(0)
  client.wfile.write("AXIS:%s,%s,%s\n" % (FLAGS.axis, FLAGS.axis_xlabel,
                                          FLAGS.axis_ylabel))
  if FLAGS.color:
    client.wfile.write("color:%s\n" % FLAGS.color)
  if FLAGS.label:
    client.wfile.write("label:%s\n" % FLAGS.label)
  if FLAGS.style:
    client.wfile.write("%s\n" % FLAGS.style.replace(',', '\n'))
  client.wfile.write("BEGIN\n")
  return client


def main():
  parse_args()

  client = None
  count = 0

  while True:
    if not client:
      client = connect_to_grapher()

    if FLAGS.command:
      cmd = FLAGS.command.format(i=count)
      value = os.popen(cmd, 'r').read()
      client.wfile.write(value)
      logging.info("Send to %s:%s '%s'", FLAGS.hostname,
                   FLAGS.port, value.strip())
      # wait before re-running command
      time.sleep(FLAGS.interval)
    else:
      # just read from stdin
      value = sys.stdin.readline()
      if value == "":
        break
      # do not sleep, read as quickly as possible
      client.wfile.write(value)

    if len(value) > 0:
      count += 1
    if FLAGS.pivot is not None:
      if count % FLAGS.pivot == 0:
        client.finish()
        client = None

if __name__ == "__main__":
  main()
