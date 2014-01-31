Pipeline View & Probe
=======================

Pipeline provides a pair of commands: lineview and lineprobe. Together,
they make it easy to view streams of data in real time from the command line.

Lineview combines SocketServer to manage client connections and pylab to plot
and display data. Multiple lineprobe clients can connect to a single server.

`lineview.py` 

* Lineview is a threaded display server. It supports a simple, text-based
  protocol, implemented by lineprobe.

  See: `lineview.py --helpshort` for more detailed usage notes.

`lineprobe.py`

* Lineprobe is a command line client that sends values to the lineview
  server. By default, lineprobe reads from stdin.  However, lineprobe can
  also run a command and read the command output instead.

  See: `lineprobe.py --helpshort` for more detailed usage notes.

Install
=======

Pipeline has two dependencies on third-party modules:

 * [matplotlib](http://www.matplotlib.org/)
  - packaged as python-matplotlib or py-matplotlib or similar.
 * [gflags](https://code.google.com/p/python-gflags/)
  - packaged as python-gflags or py-gflags or similar.

Example
=======

![Pipeline Example](https://github.com/stephen-soltesz/pipeline/raw/master/example.png)

The above example was created using commands like those below.

First, start the server:

    ./lineview.py --timestamp

Next run a lineprobe for each line. Please note that the lineprobe commands
expect scripts `sysctl.py` and `cpu.py` which return a single floating point
value and exit.

    LAB=("1" "5" "15")
    for i in 0 1 2 ; do 
      ./lineprobe.py --axis_ylabel "Load Average" \
          --label load${LAB[$i]} \
          --command "./sysctl.py $i" & 
      sleep 10
    done

Finally, read cpu load from stdin and add to a new axis named "cpu_pct".

    LAB=("sys" "user")
    for i in 0 1 ; do 
      ./cpu.py ${LAB[$i]} | ./lineprobe.py --axis_ylabel "% Load" \
          --label ${LAB[$i]} \
          --axis cpu_pct &
      sleep 1
    done


