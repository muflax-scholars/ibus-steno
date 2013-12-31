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

      # set up stroke handling
      self.__down_keys = set()
      self.__up_keys   = set()

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
      "keycode_to_steno": {
        # qwerty keys for reference
        2: "S-",     # 1
        3: "T-",     # 2
        4: "P-",     # 3
        5: "H-",     # 4
        6: "*",      # 5
        7: "#",      # 6
        8: "-F",     # 7
        9: "-P",     # 8
        10: "-L",    # 9
        11: "-T",    # 0
        12: "-D",    # -
        13: "-T -D", # =

        16: "S-",    # q
        17: "K-",    # w
        18: "W-",    # e
        19: "R-",    # r
        20: "*",     # t
        21: "*",     # y
        22: "-R",    # u
        23: "-B",    # i
        24: "-G",    # o
        25: "-S",    # p
        26: "-Z",    # [
        27: "-S -Z", # ]

        30: "#",     # a
        31: "T- K-", # s
        32: "P- W-", # d
        33: "H- R-", # f
        34: "#",     # g
        35: "#",     # h
        36: "-F -R", # j
        37: "-P -B", # k
        38: "-L -G", # l
        39: "-T -S", # ;
        40: "-D -Z", # '

        45: "A- O-", # x
        46: "A-",    # c
        47: "O-",    # v

        49: "-E",    # n
        50: "-U",    # m
        51: "-E -U", # ,
        # 52: "-E -U", # .
      },
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

    is_release  = bool(state & modifier.RELEASE_MASK)
    is_modifier = bool(state & (~ modifier.RELEASE_MASK) & modifier.MODIFIER_MASK)

    # ignore key release events
    if is_modifier:
      return False

    if not keycode in self.__steno_keycodes():
      return False

    if is_release:
      # FIXME disable auto-repeat somehow >:<
      self.__up_keys.add(keycode)
      # remove invalid released keys
      # self.__up_keys = self.__up_keys.intersection(self._down_keys)
    else:
      self.__down_keys.add(keycode)

    # handle the stroke once all keys are released
    if self.__down_keys == self.__up_keys:
      # map pressed keys into steno keys and split multi-key keys into individual keys.
      steno_keys = []
      for k in self.__down_keys:
        if k in self.__config["keycode_to_steno"]:
          steno_keys.extend(self.__config["keycode_to_steno"][k].split(" "))
      self.__reset_key_state()

      # parse the stroke
      if self.__debug:
        print "steno: ", steno_keys
      #     self.__preedit_string += unichr(keyval)
      #     self.__invalidate()
      #     self.__commit_string(self.__preedit_string)

    return True

  def __steno_keycodes(self):
    # TODO cache this?
    return set(self.__config["keycode_to_steno"].keys())

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
    self.__reset_key_state()

  def __reset_key_state(self):
    self.__down_keys.clear()
    self.__up_keys.clear()

  def property_activate(self, prop_name):
    if self.__debug:
      print "PropertyActivate(%s)" % prop_name
