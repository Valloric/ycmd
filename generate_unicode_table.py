#!/usr/bin/env python
#
# Copyright (C) 2018 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import platform
import random
import string
import subprocess
import tempfile
import unicodedata


DIR_OF_THIS_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )
DIR_OF_CPP_SOURCES = os.path.join( DIR_OF_THIS_SCRIPT, 'cpp', 'ycm' )
# See https://docs.python.org/3.6/library/functions.html#chr
MAX_UNICODE_VALUE = 1114111
UNICODE_TABLE_TEMPLATE = (
"""// This file was automatically generated with the generate_unicode_table.py
// script using version {unicode_version} of the Unicode Character Database.
static const std::array< const RawCharacter, {size} > characters = {{ {{
{characters}
}} }};""" )


def GetCharacters():
  characters = []
  for i in range( MAX_UNICODE_VALUE + 1 ):
    character = chr( i )
    lower_character = character.lower()
    upper_character = character.upper()
    swapped_character = character.swapcase()
    category = unicodedata.category( character )
    if ( character != lower_character or
         character != upper_character or
         character != swapped_character or
         category.startswith( 'L' ) or
         category.startswith( 'P' ) ):
      characters.append( {
        'original': character,
        'uppercase': upper_character,
        'swapped_case': swapped_character,
        'is_letter': category.startswith( 'L' ),
        'is_punctuation': category.startswith( 'P' ),
        'is_uppercase': character != lower_character
      } )
  return characters


def CppChar( character ):
  return '"{0}"'.format( character.replace( '\\',
                                            '\\\\' ).replace( '"', '\\"' ) )


def CppBool( statement ):
  # We use 1/0 for C++ booleans instead of true/false to reduce the size of the
  # generated table.
  if statement:
    return '1'
  return '0'


def GenerateUnicodeTable( header_path, characters ):
  unicode_version = unicodedata.unidata_version
  size = len( characters )
  characters = '\n'.join( [
    ( '{' + CppChar( character[ 'original' ] ) + ',' +
            CppChar( character[ 'uppercase' ] ) + ',' +
            CppChar( character[ 'swapped_case' ] ) + ',' +
            CppBool( character[ 'is_letter' ] ) + ',' +
            CppBool( character[ 'is_punctuation' ] ) + ',' +
            CppBool( character[ 'is_uppercase' ] ) + '},' )
    for character in characters ] )
  contents = UNICODE_TABLE_TEMPLATE.format( unicode_version = unicode_version,
                                            size = size,
                                            characters = characters )
  with open( header_path, 'w', newline = '\n', encoding='utf8' ) as header_file:
    header_file.write( contents )


def Main():
  characters = GetCharacters()
  table_path = os.path.join( DIR_OF_CPP_SOURCES, 'UnicodeTable.inc' )
  GenerateUnicodeTable( table_path, characters )


if __name__ == '__main__':
  Main()
