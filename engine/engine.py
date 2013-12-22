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
      self.__config  = self.load_config()
      self.__dict    = self.load_dict()
      self.__prop_list = self.load_props()

      print "ibus-steno ready to roll"
    except Exception as e:
      print traceback.format_exc()

  def load_config(self):
    "load / initialize user config"

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
    dict = {}
    user_dict = os.path.join(self.__config_dir, self.__config["dictionary"])
    if os.path.exists(user_dict):
      with open(user_dict) as f:
        dict.update(json.load(f))

    return dict

  def load_props(self):
    props = ibus.PropList()

    # input_mode_prop = ibus.Property(key=u"InputMode",
    #                 type=ibus.PROP_TYPE_MENU,
    #                 label=u"あ",
    #                 tooltip=_(u"Switch input mode"))
    # self.__prop_dict[u"InputMode"] = input_mode_prop

    # props = ibus.PropList()
    # props.append(ibus.Property(key=u"InputMode.Latin",
    #              type=ibus.PROP_TYPE_RADIO,
    #              label=_(u"Latin")))
    # props.append(ibus.Property(key=u"InputMode.Hiragana",
    #              type=ibus.PROP_TYPE_RADIO,
    #              label=_(u"Hiragana")))
    # props.append(ibus.Property(key=u"InputMode.Katakana",
    #              type=ibus.PROP_TYPE_RADIO,
    #              label=_(u"Katakana")))

    for prop in props:
      self.__prop_dict[prop.key] = prop

    # prop_name = self.__input_mode_prop_names[self.__tutcode.input_mode]
    # self.__prop_dict[prop_name].set_state(ibus.PROP_STATE_CHECKED)

    # input_mode_prop.set_sub_props(props)
    # tutcode_props.append(input_mode_prop)

    return props

  # def __get_clipboard(self, clipboard, text, data):
  #   clipboard_text = clipboard.wait_for_text()
  #   if clipboard_text:
  #     handled, output = \
  #               self.__tutcode.append_text(clipboard_text.decode('UTF-8'))
  #     self.__check_handled(handled, output)

  def do_process_key_event(self, keyval, keycode, state):
    "handle raw key events"
    print "process_key_event(%04x, %04x, %04x)" % (keyval, keycode, state)
    # ignore key release events
    is_press = ((state & ibus.ModifierType.RELEASE_MASK) == 0)
    if not is_press:
      return False

    if self.__preedit_string:
      if keyval == keysyms.Return:
        self.__commit_string(self.__preedit_string)
        return True
      elif keyval == keysyms.Escape:
        self.__preedit_string = u""
        self.__update()
        return True
      elif keyval == keysyms.BackSpace:
        self.__preedit_string = self.__preedit_string[:-1]
        self.__invalidate()
        return True
      elif keyval == keysyms.space:
        if self.__lookup_table.get_number_of_candidates() > 0:
          self.__commit_string(self.__lookup_table.get_current_candidate().text)
        else:
          self.__commit_string(self.__preedit_string)
        return False
      elif keyval >= 49 and keyval <= 57:
        #keyval >= keysyms._1 and keyval <= keysyms._9
        index = keyval - keysyms._1
        candidates = self.__lookup_table.get_canidates_in_current_page()
        if index >= len(candidates):
          return False
        candidate = candidates[index].text
        self.__commit_string(candidate)
        return True
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
    if keyval in xrange(keysyms.a, keysyms.z + 1) or \
      keyval in xrange(keysyms.A, keysyms.Z + 1):
      if state & (ibus.ModifierType.CONTROL_MASK | ibus.ModifierType.MOD1_MASK) == 0:
        self.__preedit_string += unichr(keyval)
        self.__invalidate()
        return True
    else:
      if keyval < 128 and self.__preedit_string:
        self.__commit_string(self.__preedit_string)

    return False

  def __invalidate(self):
    if self.__is_invalidate:
      return
    self.__is_invalidate = True
    GLib.idle_add(self.__update)


  def do_page_up(self):
    if self.__lookup_table.page_up():
      self.page_up_lookup_table()
      return True
    return False

  def do_page_down(self):
    if self.__lookup_table.page_down():
      self.page_down_lookup_table()
      return True
    return False

  def do_cursor_up(self):
    if self.__lookup_table.cursor_up():
      self.cursor_up_lookup_table()
      return True
    return False

  def do_cursor_down(self):
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


  def do_focus_in(self):
    print "focus_in"
    self.register_properties(self.__prop_list)

  def do_focus_out(self):
    print "focus_out"

  def do_reset(self):
    print "reset"

  def do_property_activate(self, prop_name):
    print "PropertyActivate(%s)" % prop_name
