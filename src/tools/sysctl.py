#!/usr/bin/env python

import sys
from ctypes import *
from ctypes.util import find_library

class loadavg(Structure):
  _fields_ = [("ldavg",  c_uint32 * 3),
              ("fscale", c_long)]
libc = cdll.LoadLibrary(find_library("c"))

def posix_sysctl_load(name):
    _mem = loadavg()
    _sz = c_size_t(sizeof(_mem))
    result = libc.sysctlbyname(c_char_p(name),
                               byref(_mem),
                               byref(_sz),
                               None,
                               c_size_t(0))

    if result != 0:
        raise Exception('sysctl returned with error %s' % result)
    #print _mem.ldavg[0]
    #print _mem.ldavg[1]
    #print _mem.ldavg[2]
    #print _mem.fscale
    return (float(_mem.ldavg[0])/_mem.fscale,
            float(_mem.ldavg[1])/_mem.fscale,
            float(_mem.ldavg[2])/_mem.fscale)

print posix_sysctl_load('vm.loadavg')[int(sys.argv[1])]
#print posix_sysctl_load('vm.loadavg')


