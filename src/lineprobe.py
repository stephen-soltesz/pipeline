#!/usr/bin/env python
"""
Summary:
  lineprobe.py connects to the lineview server and sends values to the
  server for plotting.  The new values are either read from stdin, or returned
  by a command executed by lineprobe.

Examples:
  Start the lineview.py server, then try one of the following.

  Read new values from STDIN - plots a sin() wave using bc:
    for i in {0..200}; do \\
        echo "s($i/(4*3.14))" | bc -l ; done \\
    | lineprobe.py

  Read new values from command every 5 seconds:
    lineprobe.py --interval 0.1 --command "echo 's({i}/(3.14*4))' | bc -l"

  Re-start the line after every 200 samples:
    lineprobe.py --pivot 200 --interval 0.1 --label line \\
      --command "echo 's({i}/(3.14*4))' | bc -l"

  Create a second axis on the figure:
    lineprobe.py --axis newaxis_name --interval 0.1 --label line \\
      --command "echo 's({i}/(3.14*4))' | bc -l"

  Reset the current display by wiping all data:
    lineprobe.py --reset

Usage:
  lineprobe.py [flags]
"""

import errno
import logging
import socket
import subprocess
import sys
import time

import pipeline

# third-party modules
import gflags


FLAGS = gflags.FLAGS

gflags.DEFINE_string("label", None,
    "Send specific label to lineview for this line", short_name='l')
gflags.DEFINE_string("axis", "default",
    "Use a specific axis name.", short_name='a')
gflags.DEFINE_string("axis_ylabel", "Value",
    "Use a specific axis name.", short_name='y')
gflags.DEFINE_string("axis_xlabel", "Samples",
    "Use a specific axis name.", short_name='x')
gflags.DEFINE_string("color", None,
    "Send specific color to lineview for this line", short_name='C')
gflags.DEFINE_string("style", None,
    "Send specific style hints to lineview", short_name='s')
gflags.DEFINE_bool("verbose", False,
    "Print additional status information", short_name='v')
gflags.DEFINE_string("command", None,
    "Rather than read from stdin, use output from given command.",
    short_name='c')
# TODO: need some insight into whether view is in timestamp or sample mode...
gflags.DEFINE_integer("pivot", None,
    ("Wrap all lines around given pivot point. Use with '--width' to create "
     "a fixed size window for comparing new graphs with long-running graphs."),
    short_name='P')
gflags.DEFINE_bool("reset", False,
    "Send 'RESET' command to grapher.", short_name='r')
gflags.DEFINE_bool("exit", False,
    "Send 'EXIT' command to grapher.", short_name='e')
gflags.DEFINE_float("interval", 1,
    "Delay in milliseconds between running command.",
    lower_bound=0.0, short_name='i')


def parse_args():
  """Parse args using gflags.FLAGS() and set verbose level."""
  try:
    FLAGS(sys.argv)
  except gflags.FlagsError, err:
    print '%s\nUsage: %s ARGS\n%s' % (err, sys.argv[0], FLAGS)
    sys.exit(1)

  if FLAGS.verbose:
    log_level = logging.DEBUG
  else:
    log_level = logging.INFO
  logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                      level=log_level)


def handle_streamsocket_error(error):
  print error
  if error.errno == errno.ECONNREFUSED:
    print "Is the server running at (%s,%s)?" % (FLAGS.hostname, FLAGS.port)
    print "To see usage information use:"
    print "  %s --helpshort" % sys.argv[0]
  # raise last exception
  raise


def connect_to_grapher(streamsocket=None):
  """sets up connection to server and sends initial command & style."""
  if streamsocket is None:
    try:
      client = pipeline.StreamSocket(FLAGS.hostname, FLAGS.port)
    except socket.error as error:
      handle_streamsocket_error(error)
  else:
    client = streamsocket

  if FLAGS.reset:
    client.wfile.write("RESET\n")
    sys.exit(0)
  if FLAGS.exit:
    client.wfile.write("EXIT\n")
    sys.exit(0)

  client.wfile.write("AXIS:%s,%s,%s\n" % (FLAGS.axis, FLAGS.axis_xlabel,
                                          FLAGS.axis_ylabel))
  if FLAGS.color:
    client.wfile.write("color:%s\n" % FLAGS.color)
  if FLAGS.label:
    client.wfile.write("label:%s\n" % FLAGS.label)
  if FLAGS.style:
    client.wfile.write("%s\n" % FLAGS.style.replace(',', '\n'))
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
      (value, _) = subprocess.Popen(cmd, shell=True,
                                    stdout=subprocess.PIPE).communicate()
      client.wfile.write(value)
      logging.debug("Send to %s:%s '%s'", FLAGS.hostname,
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
