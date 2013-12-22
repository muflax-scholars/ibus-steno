#!/usr/bin/env python2
#
# ibus-steno - Steno engine for IBus
#
# Copyright (c) 2013 muflax <mail@muflax.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import os
import sys
import getopt
import locale
import ibus
import gobject
import factory

class IMApp:
  def __init__(self, exec_by_ibus, debug=False):
    self.__component = ibus.Component("org.freedesktop.IBus.Steno",
                                      "Steno Component",
                                      "0.1.0",
                                      "GPL",
                                      "muflax <mail@muflax.com>",
                                      "http://github.com/muflax/ibus-steno")
    self.__component.add_engine("steno",
                                "steno",
                                "Steno",
                                "en",
                                "GPL",
                                "muflax <mail@muflax.com>",
                                "",
                                "us")

    self.__debug = debug
    self.__mainloop = gobject.MainLoop()
    self.__bus = ibus.Bus()
    self.__bus.connect("disconnected", self.__bus_disconnected_cb)
    self.__factory = factory.EngineFactory(self.__bus, self.__debug)
    if exec_by_ibus:
      if self.__debug:
        print "hooking up with IBus..."
      self.__bus.request_name("org.freedesktop.IBus.Steno", 0)
    else:
      if self.__debug:
        print "registering bus..."
      self.__bus.register_component(self.__component)

  def run(self):
    if self.__debug:
      print "starting main loop..."

    self.__mainloop.run()

  def __bus_disconnected_cb(self, bus):
    self.__mainloop.quit()

def launch_engine(exec_by_ibus, debug=False):
  IMApp(exec_by_ibus, debug).run()

def print_help(out, v = 0):
  print >> out, "-i, --ibus         executed by IBus."
  print >> out, "-h, --help         show this message."
  print >> out, "-d, --daemonize    daemonize ibus"
  print >> out, "-v, --verbose      verbose output"
  sys.exit(v)

def main():
  try:
    locale.setlocale(locale.LC_ALL, "")
  except:
    pass

  exec_by_ibus = False
  daemonize    = False
  debug        = False

  shortopt = "ihdv"
  longopt  = ["ibus", "help", "daemonize", "verbose"]

  try:
    opts, args = getopt.getopt(sys.argv[1:], shortopt, longopt)
  except getopt.GetoptError, err:
    print_help(sys.stderr, 1)

  for o, a in opts:
    if o in ("-h", "--help"):
      print_help(sys.stdout)
    elif o in ("-d", "--daemonize"):
      daemonize = True
    elif o in ("-i", "--ibus"):
      exec_by_ibus = True
    elif o in ("-v", "--verbose"):
      debug = True
    else:
      print >> sys.stderr, "Unknown argument: %s" % o
      print_help(sys.stderr, 1)

  if daemonize:
    if os.fork():
      sys.exit()

  launch_engine(exec_by_ibus, debug)

if __name__ == "__main__":
  main()
0