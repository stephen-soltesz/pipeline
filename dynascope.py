#!/usr/bin/env python

import socket
import sys
import threading
import time
import SocketServer

# remove old version of numpy from path
filter_list = ['/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python']
sys.path = filter(lambda x: x not in filter_list, sys.path)

import matplotlib
matplotlib.use("tkagg")

import pylab
from pylab import *
from datetime import datetime

class D:
  pass

p = D()

stream_data = {}
p.fig = None
p.ax = None
p.line1 = None
ctrl_c = False
last_data_len = 0

xvalues  = [ x for x in range(100) ]
y1values = [0 for x in range(100)]
y2values = [0 for x in range(100)]

def TS():
  return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
  """Client handler to receive data for display."""

  def handle(self):
    global stream_data

    cur_thread = threading.current_thread()
    cur_name = cur_thread.name
    
    if cur_name not in stream_data:
      # TODO: get name from client
      stream_data[cur_name] = {'x': [], 'y': []}

    while True:
      data = self.rfile.readline().strip()
      if data == "": break

      print "[%s-%s] %s: %s" % (cur_name, self.client_address[0], TS(),
          float(data))

      stream_data[cur_name]['x'].append(int(time.time()))
      stream_data[cur_name]['y'].append(float(data))

      #self.wfile.write(".\n")

    print cur_name, ": EXITING"

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
  # ctrl-c to main thread cleans up all threads.
  daemon_threads = True
  # much faster rebinding
  allow_reuse_address = True

  #def server_bind(self):
  #    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  #    self.socket.bind(self.server_address)

def initialize_pylab():
  xAchse=pylab.arange(0,100,1)
  yAchse=pylab.array([0]*100)

  yMIN=-1
  yMAX=1

  p.fig = pylab.figure(1)
  p.ax = p.fig.add_subplot(111)
  p.ax.grid(True)
  p.ax.set_title("Realtime Waveform Plot")
  p.ax.set_xlabel("Time")
  p.ax.set_ylabel("Amplitude")
  p.ax.axis([0,100,-1,1])
  p.line1, = p.ax.plot(xAchse,yAchse,'-')
  #line2 = ax.plot(xAchse,yAchse,'.')
  def on_key(event):
    print('you pressed', event.key, event.xdata, event.ydata)

  cid = p.fig.canvas.mpl_connect('key_press_event', on_key)

  timer = p.fig.canvas.new_timer(interval=80)
  timer.add_callback(plot_refresh, ())
  timer.start()
  print "SHOW"
  #pylab.ion()
  pylab.show()
  print "AFTER"


def plot_refresh(unused_a):
  global xvalues,y1values,y2values,p,ctrl_c,last_data_len
  try:
    plot_refresh_handler(unused_a)
  except KeyboardInterrupt as e:
    print "ctrl-c"
    sys.exit(1)
  except:
    raise

  return


def plot_refresh_handler(unused_a):
  global xvalues,y1values,y2values,p,ctrl_c,last_data_len

  if ctrl_c:
    sys.exit(1)

  if "Thread-2" not in stream_data:
    #print "skipping plot_refresh..."
    return

  if 'y' not in stream_data["Thread-2"] or len(stream_data["Thread-2"]['y']) == 0:
    print "no data yet..."
    return

  curr_data_len = len(stream_data["Thread-2"]['x'])
  if last_data_len >= curr_data_len:
    #print "last len fail"
    return

  last_data_len = curr_data_len

  x = pylab.array(stream_data['Thread-2']['x'][-100:])
  x_len = len(x)
  y = pylab.array(stream_data['Thread-2']['y'][-max(100,x_len):])

  x_min = min(x)
  x_max = max(x)

  y_min = min(y)
  y_max = max(y)

  print "len x:", last_data_len

  p.line1.set_data(x,y)

  p.ax.axis([x_min-1,
             x_max+1,
             y_min-1,
             y_max+1])

  manager = pylab.get_current_fig_manager()
  manager.canvas.draw()

def initialize_server(server):
  server.serve_forever()

if __name__ == "__main__":
  HOST, PORT = "localhost", 3131

  server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
  ip, port = server.server_address

  server_thread = threading.Thread(target=initialize_server, args=(server,))
  server_thread.setDaemon(True)

  #try:
  server_thread.start()
  print "after server"

  initialize_pylab()
  server.shutdown()
  #except KeyboardInterrupt:
  #  print "ctrl-c"
  #  ctrl_c=True
  #  sys.exit(1)
  #except:
  #  print "WTF?"
  #  sys.exit(1)

  # Start a thread with the server -- that thread will then start one
  # more thread for each request
  # server_thread = threading.Thread(target=server.serve_forever)
  # Exit the server thread when the main thread terminates
  #server_thread.daemon = True
  #server_thread.start()
  #print "Server loop running in thread:", server_thread.name

  #client(ip, port, "Hello World 1")
  #client(ip, port, "Hello World 2")
  #client(ip, port, "Hello World 3")
  #
  # server.shutdown()

#def client(ip, port, message):
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.connect((ip, port))
#    try:
#        sock.sendall(message)
#        response = sock.recv(1024)
#        print "Received: {}".format(response)
#    finally:
#        sock.close()

