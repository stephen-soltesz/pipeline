dynascope
=========

Dynascope is a pair of commands that allow you to plot a sequence of values in
real time from the command line. Dynascope was written with scripting in mind
and designed to conveniently *see* data without extra steps. Please see the
command help messages for more hints on usage.

scopeview - a server that receives data from scopeprobe and displays the lines
    as new data arrives.  Scopeview supports two modes: samples and timestamp.
    In timestamp mode, each new value received from a client is assigned a
    current timestamp. Lines are plotted using the timestamp as the x-axis
    value. Samples mode ignores delays between values and simply accumulates
    samples.

scopeprobe - a command line client that sends values to the scopeview server.
    scopeprobe can either reads from stdin, or the output from a command. If
    scopeprobe is given a command to run, you may optionally specify the
    interval.
