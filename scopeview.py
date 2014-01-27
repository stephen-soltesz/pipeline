#!/usr/bin/env python
"""
Summary:
  scopeview.py is a simple server that accepts client connections and plots
  client data in real time using pylab for display.
  
  By default, each scopeprobe client creates a separate line.

  The client protocol is simple and documented in the protocol spec. The
  simplest client would connect to the server and write strings:
    BEGIN\\n
    <float1>\\n
    <float2>\\n
  Where float1 and float2 are strings that will convert using float().

Usage - default:
  Start scopeview.py with no arguments for default options.

Usage - plot with timestamps:
  By default, the sequence order of values received by the server defines a
  value's x-coordinate. With the --timestamp option, the server associates a
  timestamp with each received value. The timestamp serves as the x-coordinate.

    ./scopeview.py --timestamp

Usage - multiple axes:
  By default a single axis is used for all lines.  You may specify multiple
  additional axes with the '--axis <name>' option to scopeprobe.py:

    ./scopeprobe.py --axix <name> [args]

Usage:
  scopeview.py [flags]
"""

import gflags
import logging
import matplotlib
# set pylab backend *before* importing pylab
#matplotlib.use("tkagg")
matplotlib.use("webagg")  # displays in browser, can be viewed by others.
import numpy
import pylab
import SocketServer
import sys
import threading
import time


DEFAULT_WIDTH = 200
HOST = "localhost"
PORT = 3131

FLAGS = gflags.FLAGS
gflags.DEFINE_integer("width", DEFAULT_WIDTH,
    "Default number of samples to show in plot.",
    short_name='w')
gflags.DEFINE_bool("timestamp", False,
    "Plot points with current timestamp on x-axis.",
    short_name='t')
gflags.DEFINE_bool("logy", False,
    "Plot the y-axis on the log scale.",
    short_name='l')
gflags.DEFINE_integer("ymin", None,
    "Plot the y-axis on the log scale.")
gflags.DEFINE_integer("ymax", None,
    "Plot the y-axis on the log scale.")
gflags.DEFINE_integer("port", PORT,
    "Default port to listen.", short_name='p')
gflags.DEFINE_string("hostname", HOST,
    "Default port to listen.", short_name='h')

# TODO: add verbose logging options
# TODO: 'reset' button
# TODO: 'zoom' y-axis
# TODO: do we want to move 'timestamp' handling to probe?
# TODO: export/save current data to text file, or send it to the client?
#       and, allow something like a 'replay'/redisplay feature?



def parse_args():
  """invokes gflags.FLAGS() on sys.argv."""
  try:
    FLAGS(sys.argv)
  except gflags.FlagsError as err:
    print err
    print '%s\nUsage: %s ARGS\n%s' % (err, sys.argv[0], FLAGS)
    sys.exit(1)

  logging.basicConfig(format = '[%(asctime)s] %(levelname)s: %(message)s',
      level = logging.INFO)


def timestamp():
  """return a string timestamp in YYYY-MM-DDTHH:MM:SS form."""
  return time.strftime("%Y-%m-%dT%H:%M:%S")


def get_threadname():
  """return current thread name."""
  cur_thread = threading.current_thread()
  return cur_thread.name


def find_uniq_preserve_order(orig_keys, orig_values=None):
  """remove duplicate keys while preserving order. optionally return values."""
  seen = {}
  keys = []
  values = []
  for i, item in enumerate(orig_keys):
    if item in seen:
      continue
    seen[item] = 1
    keys.append(item)
    if orig_values:
      values.append(orig_values[i])
  return keys, values


class ScoperThreadedClientProbeHandler(SocketServer.StreamRequestHandler):
  """Client handler to receive data for display."""

  def _handle_reset(self):
    """resets server figure by deleting lines and clearing legend."""
    stream_data = self.server.stream_data
    # remove lines from graph, and reset legends
    for name in stream_data:
      stream_data[name]['line'].remove()
    for name in self.server.axes:
      self.server.axes[name].legend([])  # TODO: find a better way.
    stream_data = {}

  def _handle_update_legend(self, single_axes):
    """Updates the legend for single_axes, listing duplicate labels once."""
    # lines are bundled with an axes.
    # legends are printed per axes.
    # line data is in stream_data without reference to axes sets.
    # for each current line, get label, get axes
    # for unique axes-labels create a list to pass to legend()
    artists, labels = single_axes.get_legend_handles_labels()
    uniq_labels, uniq_artists = find_uniq_preserve_order(labels, artists)
    leg = single_axes.legend(uniq_artists, uniq_labels,
        bbox_to_anchor=(0., 0.91, 1., .09),
        loc=2, borderaxespad=0.)
    for text in leg.get_texts():
      text.set_fontsize('small')

  def _handle_create_line(self, axes, style_args):
    """creates a line on the given axes using style_args. returns line_name"""
    stream_data = self.server.stream_data
    # sample data for initial create
    x_data = numpy.arange(0, 2, 1)
    y_data = numpy.array([0]*2)

    line, = axes.plot(x_data, y_data, '-', **style_args)
    # NOTE: client may set 'label'
    line_name = style_args['label']
    if line_name in stream_data:
      # preserve old line data with a new name
      stream_data[line_name+"_old_"+timestamp()] = stream_data[line_name]
    # always start with no data for the new line
    stream_data[line_name] = {'y': [], 'line': line, 'last_len': 0}
    if FLAGS.timestamp:
      stream_data[line_name]['x'] = []
    return line_name

  def _handle_client_read_data(self, line_name):
    """Loops reading client data and appending it to stream_data."""
    stream_data = self.server.stream_data
    while True:
      data = self.rfile.readline().strip()
      if data == "":
        break

      # TODO: add verbose logging options
      #print "[%s-%s] %s: %s" % (thread_name, self.client_address[0],
      #    timestamp(), float(data))

      if FLAGS.timestamp:
        x_val = float(time.time())
        stream_data[line_name]['x'].append(x_val)

      y_val = float(data)
      stream_data[line_name]['y'].append(y_val)
      #self.wfile.write(".\n")

  def _handle_client_init(self, style_args, axis_args):
    """Read client initialization: axes, style, or reset commands."""
    while True:
      data = self.rfile.readline().strip()
      if data == "":
        return

      fields = data.split(":")
      if "EXIT" in fields:
        self.server.flags.exit = True
        return "RETURN"

      if "RESET" in fields:
        self._handle_reset()
        # NOTE: reset does nothing else, so return/exit from thread
        return "RETURN"

      if "AXIS" in fields:
        axis_fields = fields[1].split(",")
        assert(len(axis_fields) == 3)
        axis_name, x_label, y_label = axis_fields
        axis_args['name'] = axis_name
        axis_args['x_label'] = x_label
        axis_args['y_label'] = y_label
        continue

      if "BEGIN" in fields:
        break

      try:
        style_args[fields[0]] = float(fields[1])
      except ValueError as _:
        style_args[fields[0]] = fields[1]

    return "CONTINUE"

  def _handle_setup_axis(self, axis_args):
    """Add a new axis, if axis_args are not already created."""
    axis_name = axis_args['name']
    axes_dict = self.server.axes

    if axis_name not in [name for name, _ in axes_dict.items()]:
      print "Adding a new axis:", axis_name
      axis_count = len(axes_dict)
      newaxis = self.server.figure.add_subplot(axis_count+1, 1, axis_count+1)
      axes_dict[axis_name] = newaxis
      axes_dict[axis_name].grid(True)
      axes_dict[axis_name].set_xlabel(axis_args['x_label'])
      axes_dict[axis_name].set_ylabel(axis_args['y_label'])
      # TODO: support *.set_title("Scoper")
      if FLAGS.logy:
        axes_dict[axis_name].set_yscale('log', nonposy='clip')

      if axis_count != 0:
        # Resize other axes if the above wasn't the first.
        axis_count = len(axes_dict)
        for row,(name, _) in enumerate(axes_dict.items(), 1):
          print name, axis_count, row
          axes_dict[name].change_geometry(axis_count, 1, row)

  def handle(self):
    """SocketServer handler, called when clients connect."""
    thread_name = get_threadname()

    style_args = {}
    style_args['label'] = thread_name

    axis_args = {}
    axis_args['name'] = 'default'
    axis_args['x_label'] = ''
    axis_args['y_label'] = ''

    # client_init blocks until client sends 'BEGIN'
    status = self._handle_client_init(style_args, axis_args)
    if status == "RETURN":
      # done with client
      return

    self._handle_setup_axis(axis_args)

    print "Assigning to axis:", axis_args['name']
    axes = self.server.axes[axis_args['name']]
    line_name = self._handle_create_line(axes, style_args)
    self._handle_update_legend(axes)

    # NOTE: client_read_data will block until client disconnects.
    self._handle_client_read_data(line_name)
    print "Exiting:", thread_name


class ScoperThreadedTCPServer(SocketServer.ThreadingMixIn,
                              SocketServer.TCPServer):
  """Custom TCP Server with daemon threads and allow_reuse_address enabled."""
  # let ctrl-c to main thread cleans up all threads.
  daemon_threads = True
  # let rebinding to listening port more quickly
  allow_reuse_address = True

  def setup(self, flags):
    """create instance data for figure, axes, and stream data."""
    self.figure = pylab.figure(1)
    self.axes = {}
    self.stream_data = {}
    self.flags = flags


# TODO: clean up the event handling examples here.
def pylab_setup(figure, stream_data, original_width, runlimits, runflags):
  """setup callbacks, calls pylab.show() which blocks until close or exit."""

  def on_key(event):
    """on_key"""
    print('you pressed', event.key, event.xdata, event.ydata)

  #def diag_event(event):
  #  """diag_event"""
  #  print event.name
  #  if hasattr(event, 'height'):
  #    print event.height, event.width
  #  print event.name, event.canvas, event.guiEvent

  def pause_axis(unused_event):
    """pause_axis"""
    # stops update of axis when updating lines
    # allows smooth scrolling by user
    print "PAUSE pause axis"
    runflags.update_axis = False

  def unpause_axis(event):
    """unpause_axis"""
    # continues updating scrolling
    print "RESUME axis"
    runflags.update_axis = True
    if hasattr(event, 'height'):
      print event.height, event.width
    new_ratio = float(event.width)/float(event.height)
    default_ratio = 1.3
    print "BEFORE: ", FLAGS.width
    FLAGS.width = original_width * new_ratio / default_ratio
    print "AFTER: ", FLAGS.width

  figure.canvas.mpl_connect('key_press_event', on_key)
  figure.canvas.mpl_connect('resize_event', unpause_axis)
  figure.canvas.mpl_connect('scroll_event', pause_axis)

  timer = figure.canvas.new_timer(interval=500)
  timer.add_callback(plot_refresh_handler, (stream_data, runlimits, runflags))
  timer.start()
  print "SHOW"
  pylab.show()
  print "AFTER"


class Flags(object):
  """Flags shared across threads."""
  def __init__(self):
    self.exit = False
    self.update_axis = True


class Limits(object):
  """Container class for global axes limits"""
  def __init__(self):
    self.x_min = sys.maxint
    self.x_max = 0
    self.y_min = sys.maxint
    self.y_max = 0


def plot_refresh_handler(args):
  """Timer callback for redrawing plots with latest data."""
  stream_data, runlimits, runflags = args
  if runflags.exit:
    sys.exit(1)

  for line_name in stream_data:
    data = stream_data[line_name]
    curr_data_len = len(data['y'])
    if curr_data_len == 0:
      # no data yet
      continue

    if data['last_len'] >= curr_data_len:
      # no new data since last update
      continue

    # save length of last line draw
    data['last_len'] = curr_data_len

    if FLAGS.timestamp:
      x_data = numpy.array(data['x'])
    else:
      x_data = numpy.array(range(curr_data_len))
    y_data = numpy.array(data['y'])

    runlimits.x_max = max(max(x_data), runlimits.x_max)
    runlimits.x_min = runlimits.x_max-FLAGS.width

    if FLAGS.ymin is not None:
      runlimits.y_min = FLAGS.ymin
    else:
      runlimits.y_min = min(min(y_data), runlimits.y_min)

    if FLAGS.ymax is not None:
      runlimits.y_max = FLAGS.ymax
    else:
      runlimits.y_max = max(max(y_data), runlimits.y_max)

    data['line'].set_data(x_data, y_data)
    if runflags.update_axis:
      axes = data['line'].get_axes()
      axes.relim()
      axes.set_xlim(runlimits.x_min-1, runlimits.x_max+1)
      axes.autoscale_view(scaley=True, scalex=False)

  manager = pylab.get_current_fig_manager()
  manager.canvas.draw()

def initialize_server(server):
  server.serve_forever()

def main():
  runlimits = Limits()
  runflags = Flags()

  parse_args()

  server = ScoperThreadedTCPServer((FLAGS.hostname, FLAGS.port),
                                   ScoperThreadedClientProbeHandler)
  server.setup(runflags)

  server_thread = threading.Thread(target=initialize_server, args=(server,))
  server_thread.setDaemon(True)
  server_thread.start()

  # blocks on pylab.show()
  pylab_setup(server.figure, server.stream_data, FLAGS.width, runlimits,
              runflags)

  logging.info("Shutdown server")
  server.shutdown()

if __name__ == "__main__":
  main()

