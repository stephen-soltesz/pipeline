Pipescope View & Probe
=======================

Pipescope provides a pair of commands: scopeview and scopeprobe. Together,
they make it easy to view streams of data in real time from the command line.

Scopeview combines SocketServer to manage client connections and pylab to plot
and display data. Multiple scopeprobe clients can connect to a single server.

`scopeview.py` 

* Scopeview is a threaded display server. It supports a simple, text-based
  protocol, implemented by scopeprobe.

  See: `scopeview.py --helpshort` for more detailed usage notes.

`scopeprobe.py`

* Scopeprobe is a command line client that sends values to the scopeview
  server. By default, scopeprobe reads from stdin.  However, scopeprobe can
  also run a command and read the command output instead.

  See: `scopeprobe.py --helpshort` for more detailed usage notes.

Install
=======

Pipescope has two dependencies on third-party modules:

 * [matplotlib][http://www.matplotlib.org/]
 * [gflags][https://code.google.com/p/python-gflags/]

Example
=======

![Pipescope Example](https://github.com/stephen-soltesz/pipescope/raw/master/example.png)

The above example was created using commands like those below.

First, start the server:

    ./scopeview.py --timestamp

Next run a scopeprobe for each line. Please note that the scopeprobe commands
expect scripts `sysctl.py` and `cpu.py` which return a single floating point
value and exit.

    LAB=("1" "5" "15")
    for i in 0 1 2 ; do 
      ./scopeprobe.py --axis_ylabel "Load Average" \
          --label load${LAB[$i]} \
          --command "./sysctl.py $i" & 
      sleep 10
    done

Finally, read cpu load from stdin and add to a new axis named "cpu_pct".

    LAB=("sys" "user")
    for i in 0 1 ; do 
      ./cpu.py ${LAB[$i]} | ./scopeprobe.py --axis_ylabel "% Load" \
          --label ${LAB[$i]} \
          --axis cpu_pct &
      sleep 1
    done


