# -*- coding: utf-8 -*-
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

import os, os.path
import traceback

try:
  import simplejson as json
except ImportError :
  import json

try:
  from gtk import clipboard_get
except ImportError:
  clipboard_get = lambda a: None

import gobject
import ibus
from ibus import keysyms, modifier

class EngineSteno(ibus.EngineBase):
  def __init__(self, bus, object_path, debug=False):
    self.__debug = debug

    if self.__debug:
      print "initializing engine..."

    super(EngineSteno, self).__init__(bus, object_path)

    try:
      # initialize ibus config
      self.__is_invalidate  = False
      self.__preedit_string = u""
      self.__lookup_table   = ibus.LookupTable(10, 0, True, True)
      self.__prop_dict      = {}

      # user config
      self.__config_dir  = os.path.expanduser("~/.ibus-steno")
      self.__config_file = os.path.join(self.__config_dir, "config.json")

      # load various components
      self.__config    = self.load_config()
      self.__dict      = self.load_dict()
      self.__prop_list = self.load_props()

      print "ibus-steno ready to roll"
    except Exception as e:
      print traceback.format_exc()

  def load_config(self):
    "load / initialize user config"

    # TODO: ibus provides a config interface in self.config; use it

    if self.__debug:
      print "loadinging config at '%s'..." % self.__config_file

    # defaults
    config = {
      "dictionary": "default.json",
    }

    # create the configuration directory if needed
    if not os.path.exists(self.__config_dir):
      print "make:", self.__config_dir
      os.makedirs(self.__config_dir)

    # write config if needed
    if not os.path.exists(self.__config_file):
      with open(self.__config_file, "w") as f:
        json.dump(config, f, sort_keys=True, indent=2, separators=(",", ": "))
    else:
      # merge user config into default config
      with open(self.__config_file, "r") as f:
        try:
          config.update(json.load(f))
        except:
          print "config invalid, skipping"

    return config

  def load_dict(self):
    "initialize steno dictionary"

    if self.__debug:
      print "loading dictionary..."

    dict = {}
    user_dict = os.path.join(self.__config_dir, self.__config["dictionary"])
    if os.path.exists(user_dict):
      if self.__debug:
        print "loading dict at '%s'..." % user_dict
      with open(user_dict) as f:
        dict.update(json.load(f))

    if self.__debug:
      print "dictionary with %d entries loaded." % len(dict)

    return dict

  def load_props(self):
    if self.__debug:
      print "loading properties..."

    props = ibus.PropList()

    for prop in props:
      self.__prop_dict[prop.key] = prop

    return props

  # def __get_clipboard(self, clipboard, text, data):
  #   clipboard_text = clipboard.wait_for_text()
  #   if clipboard_text:
  #     handled, output = self.__tutcode.append_text(clipboard_text.decode('UTF-8'))
  #     self.__check_handled(handled, output)

  def process_key_event(self, keyval, keycode, state):
    "handle raw key events"

    # ignore key release events
    is_release = bool(state & modifier.RELEASE_MASK)

    # control the preedit window
    if self.__preedit_string and not is_release:
      if keyval == keysyms.Return:
        self.__commit_string(self.__preedit_string)
        return True
      elif keyval == keysyms.Escape:
        self.__preedit_string = u""
        self.__update()
        return True
      elif keyval == keysyms.BackSpace:
        self.__preedit_string = u""
        self.__update()
        return True
      elif keyval == keysyms.space:
        if self.__lookup_table.get_number_of_candidates() > 0:
          self.__commit_string(self.__lookup_table.get_current_candidate().text)
        else:
          self.__commit_string(self.__preedit_string)
        return False
      elif keyval == keysyms.Page_Up or keyval == keysyms.KP_Page_Up:
        self.page_up()
        return True
      elif keyval == keysyms.Page_Down or keyval == keysyms.KP_Page_Down:
        self.page_down()
        return True
      elif keyval == keysyms.Up:
        self.cursor_up()
        return True
      elif keyval == keysyms.Down:
        self.cursor_down()
        return True
      elif keyval == keysyms.Left or keyval == keysyms.Right:
        return True

    return self.__handle_input(keyval, keycode, state)

  def __handle_input(self, keyval, keycode, state):
    """analyzes the input, commits any text changes and then returns True/False depending on whether it's done with the event"""

    handled = True

    if self.__debug:
      print "key: %d %d %d" % (keyval, keycode, state)

    is_release  = bool(state & modifier.RELEASE_MASK)
    is_modifier = bool(state & (~ modifier.RELEASE_MASK) & modifier.MODIFIER_MASK)

    # ignore key release events
    if is_modifier:
      return False

    if self.__debug:
      print "release: ",  is_release

    # if keyval in xrange(keysyms.a, keysyms.z + 1) or \
    #   keyval in xrange(keysyms.A, keysyms.Z + 1):
    #   if state & (ModifierType.CONTROL_MASK | ModifierType.MOD1_MASK) == 0:
    #     self.__preedit_string += unichr(keyval)
    #     self.__invalidate()
    #     return True
    # else:
    #   if keyval < 128 and self.__preedit_string:
    #     self.__commit_string(self.__preedit_string)

    # self.commit_text(ibus.Text("cow"))

    return handled

  def __invalidate(self):
    if self.__is_invalidate:
      return
    self.__is_invalidate = True
    GLib.idle_add(self.__update)


  def page_up(self):
    if self.__lookup_table.page_up():
      self.page_up_lookup_table()
      return True
    return False

  def page_down(self):
    if self.__lookup_table.page_down():
      self.page_down_lookup_table()
      return True
    return False

  def cursor_up(self):
    if self.__lookup_table.cursor_up():
      self.cursor_up_lookup_table()
      return True
    return False

  def cursor_down(self):
    if self.__lookup_table.cursor_down():
      self.cursor_down_lookup_table()
      return True
    return False

  def __commit_string(self, text):
    self.commit_text(ibus.Text.new_from_string(text))
    self.__preedit_string = u""
    self.__update()

  def __update(self):
    preedit_len = len(self.__preedit_string)
    attrs = ibus.AttrList()
    self.__lookup_table.clear()
    # if preedit_len > 0:
    #   if not self.__dict.check(self.__preedit_string):
    #     attrs.append(ibus.Attribute.new(ibus.AttrType.FOREGROUND,
    #         0xff0000, 0, preedit_len))
    #     for text in self.__dict.suggest(self.__preedit_string):
    #       self.__lookup_table.append_candidate(ibus.Text.new_from_string(text))
    text = ibus.Text.new_from_string(self.__preedit_string)
    text.set_attributes(attrs)
    self.update_auxiliary_text(text, preedit_len > 0)

    attrs.append(ibus.Attribute.new(ibus.AttrType.UNDERLINE,
        ibus.AttrUnderline.SINGLE, 0, preedit_len))
    text = ibus.Text.new_from_string(self.__preedit_string)
    text.set_attributes(attrs)
    self.update_preedit_text(text, preedit_len, preedit_len > 0)
    self.__update_lookup_table()
    self.__is_invalidate = False

  def __update_lookup_table(self):
    visible = self.__lookup_table.get_number_of_candidates() > 0
    self.update_lookup_table(self.__lookup_table, visible)


  def focus_in(self):
    if self.__debug:
      print "focus_in"
    self.register_properties(self.__prop_list)

  def focus_out(self):
    if self.__debug:
      print "focus_out"

  def reset(self):
    if self.__debug:
      print "reset"

  def property_activate(self, prop_name):
    if self.__debug:
      print "PropertyActivate(%s)" % prop_name
