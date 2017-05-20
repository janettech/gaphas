#!/usr/bin/env python

# Copyright (C) 2006-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.

"""
Gaphas
======

Gaphor's Canvas.

This module contains the application independant parts of Gaphor's Canvas.
It can and may be used by others under the terms of the GNU LGPL licence.

Notes
=====

In py-cairo 1.8.0 (or 1.8.1, or 1.8.2) the multiplication order has
been reverted. This causes bugs in Gaphas.

Also a new method ``multiply()`` has been introduced. This method is
used in Gaphas instead of the multiplier (``*``). In both the ``Canvas`` and
``View`` class a workaround is provided in case an older version of py-cairo
is used.
"""

from __future__ import absolute_import

from gaphas.canvas import Canvas
from gaphas.connector import Handle
from gaphas.item import Item, Line, Element
from gaphas.view import View, GtkView

__version__ = "$Revision$"
# $HeadURL$


# vi:sw=4:et:ai
