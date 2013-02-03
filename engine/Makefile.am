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

engine_steno_PYTHON = \
	engine.py \
	main.py \
	$(NULL)
engine_stenodir = $(pkgdatadir)/engine

libexec_SCRIPTS = ibus-steno

component_DATA = steno.xml
componentdir = $(datadir)/ibus/component

CLEANFILES = \
	*.pyc \
	$(NULL)

EXTRA_DIST = \
	ibus-steno.in \
	steno.xml.in.in \
	$(NULL)

steno.xml: steno.xml.in
	$(AM_V_GEN) \
	( \
		libexecdir=${libexecdir}; \
		pkgdatadir=${pkgdatadir}; \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@
