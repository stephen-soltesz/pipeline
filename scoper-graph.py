#!/usr/bin/env python

import logging
import socket
import sys
import threading
import time
import SocketServer

import gflags
FLAGS = gflags.FLAGS

DEFAULT_WIDTH=100
DEFAULT_HEIGHT=100
gflags.DEFINE_integer("sample_width", DEFAULT_WIDTH, 
                      "Default number of samples to show in plot.", short_name='w')

# remove old version of numpy from path
import matplotlib
matplotlib.use("tkagg")

import pylab
from pylab import *
from datetime import datetime

stream_data = {}
update_axis=True

def usage():
  return "TODO: add usage()"

def parse_args():
    try:
        FLAGS(sys.argv)
    except gflags.FlagsError, err:
        print usage()
        print '%s\nUsage: %s ARGS\n%s' % (err, sys.argv[0], FLAGS)
        sys.exit(1)

#if len(sys.argv) == 1:
#        print usage()
#        print 'Usage: %s ARGS\n%s' % (sys.argv[0], FLAGS)
#        sys.exit(1)

    logging.basicConfig(format = '[%(asctime)s] %(levelname)s: %(message)s',
                        level = logging.INFO)



def TS():
  return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def get_threadname():
  cur_thread = threading.current_thread()
  return cur_thread.name


def update_legend(axes):
  leg = axes.legend(bbox_to_anchor=(0., 0.91, 1., .09),
                    loc=1, borderaxespad=0.)
  for t in leg.get_texts():
    t.set_fontsize('small')


class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
  """Client handler to receive data for display."""

  def handle(self):
    global stream_data

    cur_name = get_threadname()
    x_array = pylab.arange(0,100,1)
    y_array = pylab.array([0]*100)
    # assumed p.ax already exists.
    extra_args = {}
    extra_args['label'] = cur_name

    while True:
      data = self.rfile.readline().strip()
      if data == "": return

      fields = data.split(":")
      if "BEGIN" in fields:
        break

      try:
          extra_args[fields[0]] = float(fields[1])
      except:
          extra_args[fields[0]] = fields[1]

    line, = self.server.axes.plot(x_array, y_array, '-', **extra_args)
    update_legend(self.server.axes)

    if cur_name not in stream_data:
      # TODO: get name from client
      stream_data[cur_name] = {'x': [], 'y': [], 'line': line, 'last_len': 0}


    while True:
      data = self.rfile.readline().strip()
      if data == "": break

      print "[%s-%s] %s: %s" % (cur_name, self.client_address[0], TS(),
          float(data))

      x = float(time.time())
      y = float(data)

      stream_data[cur_name]['x'].append(x)
      stream_data[cur_name]['y'].append(y)

      #self.wfile.write(".\n")

    print cur_name, ": EXITING"

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
  # let ctrl-c to main thread cleans up all threads.
  daemon_threads = True
  # let rebinding to listening port more quickly
  allow_reuse_address = True

  def Setup(self):
    self.figure = pylab.figure(1)
    self.axes = self.figure.add_subplot(111)

def pylab_setup(figure):
  global update_axis
  for ax in figure.get_axes():
    ax.grid(True)
    ax.set_title("Scoper")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.axis([0,100,-1,1])

  def on_key(event):
    print('you pressed', event.key, event.xdata, event.ydata)

  def diag_event(event):
    print event.name
    if hasattr(event, 'height'):
      print event.height, event.width
    print event.name, event.canvas, event.guiEvent

  def pause_axis(event):
    # stops update of axis when updating lines
    # allows smooth scrolling by user
    global update_axis
    print "PAUSE pause axis"
    update_axis=False

  def unpause_axis(event):
    # continues updating scrolling
    global update_axis
    print "RESUME axis"
    update_axis=True
    if hasattr(event, 'height'):
      print event.height, event.width
    new_ratio = float(event.width)/float(event.height)
    default_ratio = 1.3
    print "BEFORE: ", FLAGS.sample_width
    FLAGS.sample_width = DEFAULT_WIDTH * new_ratio / default_ratio
    print "AFTER: ", FLAGS.sample_width

  cid = figure.canvas.mpl_connect('key_press_event', on_key)
  cid = figure.canvas.mpl_connect('resize_event', unpause_axis)
  cid = figure.canvas.mpl_connect('scroll_event', pause_axis)

  timer = figure.canvas.new_timer(interval=200)
  timer.add_callback(plot_refresh, ())
  timer.start()
  print "SHOW"
  pylab.show()
  print "AFTER"


def plot_refresh(unused_a):
  global p
  try:
    plot_refresh_handler(unused_a)
  except KeyboardInterrupt as e:
    print "ctrl-c"
    sys.exit(1)
  except:
    raise

  return


ax_min = sys.maxint
ax_max = 0

ay_min = sys.maxint
ay_max = 0

def plot_refresh_handler(unused_a):
  global ax_min, ax_max, ay_min, ay_max, update_axis

  for thread_name in stream_data:
    data = stream_data[thread_name]
    curr_data_len = len(data['y'])
    if curr_data_len == 0:
      # no data yet
      continue

    if data['last_len'] >= curr_data_len:
      # no new data since last update
      continue

    data['last_len'] = curr_data_len
    print "drawing ", thread_name
    print "len x:", data['last_len']

    #x = pylab.array(data['x'][-100:])
    #x_len = len(x)
    #y = pylab.array(data['y'][-max(100,x_len):])
    x = pylab.array(data['x'])
    y = pylab.array(data['y'])

    ax_max = max(max(x),ax_max)
    #ax_min = min(min(x),ax_max-100)
    ax_min = ax_max-FLAGS.sample_width

    ay_min = min(min(y),ay_min)
    ay_max = max(max(y),ay_max)

    data['line'].set_data(x,y)
    if update_axis:
      ax = data['line'].get_axes()
      ax.axis([ax_min-1,
               ax_max+1,
               ay_min-1,
               ay_max+1])
    else:
      print "skipping axis update"

  manager = pylab.get_current_fig_manager()
  manager.canvas.draw()

def initialize_server(server):
  server.serve_forever()

if __name__ == "__main__":
  HOST, PORT = "localhost", 3131

  parse_args()

  server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
  server.Setup()

  server_thread = threading.Thread(target=initialize_server, args=(server,))
  server_thread.setDaemon(True)

  server_thread.start()

  # pylab_setup blocks on pylab.show()
  pylab_setup(server.figure)

  print "after server"
  server.shutdown()

