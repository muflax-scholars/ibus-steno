# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import ibus
import engine
import sys, os, os.path

class EngineFactory(ibus.EngineFactoryBase):
  def __init__(self, bus, debug=False):
    self.__bus   = bus
    self.__debug = debug

    if self.__debug:
      print "initializing factory..."

    super(EngineFactory, self).__init__(self.__bus)

    self.__id = 0

    if self.__debug:
      print "...factory done!"

  def create_engine(self, engine_name):
    if engine_name == "steno":
      self.__id += 1
      return engine.EngineSteno(
        self.__bus,
        "%s/%d" % ("/org/freedesktop/IBus/Steno/Engine",
                   self.__id),
        self.__debug)

    return super(EngineFactory, self).create_engine(engine_name)