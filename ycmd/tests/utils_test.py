#!/usr/bin/env python
#
# Copyright (C) 2016  ycmd contributors.
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

# Intentionally not importing unicode_literals!
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa
from future.utils import PY2

from nose.tools import eq_, ok_
from ycmd import utils

# NOTE: isinstance() vs type() is carefully used in this test file. Before
# changing things here, read the comments in utils.ToBytes.


if PY2:
  def ToBytes_Py2Bytes_test():
    value = utils.ToBytes( bytes( 'abc' ) )
    eq_( value, bytes( 'abc' ) )
    eq_( type( value ), bytes )


  def ToBytes_Py2Str_test():
    value = utils.ToBytes( 'abc' )
    eq_( value, bytes( 'abc' ) )
    eq_( type( value ), bytes )


  def ToBytes_Py2FutureStr_test():
    value = utils.ToBytes( str( 'abc' ) )
    eq_( value, bytes( 'abc' ) )
    eq_( type( value ), bytes )


  def ToBytes_Py2Unicode_test():
    value = utils.ToBytes( u'abc' )
    eq_( value, bytes( 'abc' ) )
    eq_( type( value ), bytes )


  def ToBytes_Py2Int_test():
    value = utils.ToBytes( 123 )
    eq_( value, bytes( '123' ) )
    eq_( type( value ), bytes )


def ToBytes_Bytes_test():
  value = utils.ToBytes( bytes( b'abc' ) )
  eq_( value, bytes( b'abc' ) )
  eq_( type( value ), bytes )


def ToBytes_Str_test():
  value = utils.ToBytes( u'abc' )
  eq_( value, bytes( b'abc' ) )
  eq_( type( value ), bytes )


def ToBytes_Int_test():
  value = utils.ToBytes( 123 )
  eq_( value, bytes( b'123' ) )
  eq_( type( value ), bytes )


if PY2:
  def ToUnicode_Py2Bytes_test():
    value = utils.ToUnicode( bytes( 'abc' ) )
    eq_( value, u'abc' )
    ok_( isinstance( value, str ) )


  def ToUnicode_Py2Str_test():
    value = utils.ToUnicode( 'abc' )
    eq_( value, u'abc' )
    ok_( isinstance( value, str ) )


  def ToUnicode_Py2FutureStr_test():
    value = utils.ToUnicode( str( 'abc' ) )
    eq_( value, u'abc' )
    ok_( isinstance( value, str ) )


  def ToUnicode_Py2Unicode_test():
    value = utils.ToUnicode( u'abc' )
    eq_( value, u'abc' )
    ok_( isinstance( value, str ) )


  def ToUnicode_Py2Int_test():
    value = utils.ToUnicode( 123 )
    eq_( value, u'123' )
    ok_( isinstance( value, str ) )


def ToUnicode_Bytes_test():
  value = utils.ToUnicode( bytes( b'abc' ) )
  eq_( value, u'abc' )
  ok_( isinstance( value, str ) )


def ToUnicode_Str_test():
  value = utils.ToUnicode( u'abc' )
  eq_( value, u'abc' )
  ok_( isinstance( value, str ) )


def ToUnicode_Int_test():
  value = utils.ToUnicode( 123 )
  eq_( value, u'123' )
  ok_( isinstance( value, str ) )
