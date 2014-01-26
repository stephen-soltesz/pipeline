Pylabscope View & Probe
=======================

Pylabscope provides a pair of commands: scopeview and scopeprobe. Together,
they make it easy to view streams of data in real time from the command line.

Scopeview combines SocketServer to manage client connections and pylab to plot
and display data. Multiple scopeprobe clients can connect to a single server.

`scopeview.py` 

  Scopeview is a threaded display server. It supports a simple, text-based
  protocol, implemented by scopeprobe.

  See: `scopeview.py --helpshort` for more detailed usage notes.

`scopeprobe.py`

  Scopeprobe is a command line client that sends values to the scopeview
  server. By default, scopeprobe reads from stdin.  However, scopeprobe can
  also run a command and read the command output instead.

  See: `scopeprobe.py --helpshort` for more detailed usage notes.

