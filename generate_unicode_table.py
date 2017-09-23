#!/usr/bin/env python

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
BINARY_SEARCH_TEMPLATE = (
"""// This file was automatically generated with the generate_unicode_table.py
// script.
//
// Copyright (C) {year} ycmd contributors
//
// This file is part of ycmd.
//
// ycmd is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// ycmd is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

#ifndef UNICODE_TABLE_H_{header_hash}
#define UNICODE_TABLE_H_{header_hash}

#include <array>
#include <cstring>

namespace YouCompleteMe {{

typedef struct RawCharacter {{
  const char *original;
  const char *lowercase;
  const char *uppercase;
  bool is_letter;
  bool is_punctuation;
  bool is_uppercase;
}} RawCharacter;

class UnicodeTable {{

public:
  static const RawCharacter Find( const char *text );

}};

const RawCharacter UnicodeTable::Find( const char *text ) {{
  static const std::array< RawCharacter, {size} > characters = {{ {{
{characters}
  }} }};

  // Do a binary search on the array of characters to find the raw character
  // corresponding to the text. If no character is found, return an empty raw
  // character.
  auto first = characters.begin();
  auto last = characters.end();
  unsigned count = last - first, step;
  auto it = first;
  int cmp;

  while ( count > 0 ) {{
    it = first;
    step = count / 2;
    it += step;
    cmp = std::strcmp( it->original, text );
    if ( cmp == 0 )
      return *it;
    if ( cmp < 0 ) {{
      first = ++it;
      count -= step + 1;
    }} else
      count = step;
  }}

  if ( first != last && std::strcmp( first->original, text ) == 0 )
    return *first;
  return {{ nullptr, nullptr, nullptr, 0, 0, 0 }};
}}

}} // namespace YouCompleteMe

#endif /* end of include guard: UNICODE_TABLE_H_{header_hash} */""" )


def GetCharacters():
  # Valid range for chr. See
  # https://docs.python.org/3.6/library/functions.html#chr
  characters = []
  for i in range( 114112 ):
    character = chr( i )
    lower_character = character.lower()
    upper_character = character.upper()
    category = unicodedata.category( character )
    if ( character != lower_character or character != upper_character or
         category.startswith( 'L' ) or category.startswith( 'P' ) ):
      characters.append( {
        'original': character,
        'lowercase': lower_character,
        'uppercase': upper_character,
        'is_letter': category.startswith( 'L' ),
        'is_punctuation': category.startswith( 'P' ),
        'is_uppercase': character != lower_character
      } )
  return characters


def CppChar( character ):
  return '"{0}"'.format( character.replace( '\\',
                                            '\\\\' ).replace( '"', '\\"' ) )


def CppBool( statement ):
  if statement:
    return '1'
  return '0'


def GenerateRandomHeaderHash():
  return ''.join(
    [ random.choice( string.ascii_uppercase + string.digits )
      for i in range( 8 ) ] )


def GenerateUnicodeTable( header_path, characters ):
  size = len( characters )
  characters = '\n'.join( [
    ( '    { ' + CppChar( character[ 'original' ] ) + ', ' +
                 CppChar( character[ 'lowercase' ] ) + ', ' +
                 CppChar( character[ 'uppercase' ] ) + ', ' +
                 CppBool( character[ 'is_letter' ] ) + ', ' +
                 CppBool( character[ 'is_punctuation' ] ) + ', ' +
                 CppBool( character[ 'is_uppercase' ] ) + ' },' )
    for character in characters ] )
  header_hash = GenerateRandomHeaderHash()
  year = datetime.datetime.now().year
  contents = BINARY_SEARCH_TEMPLATE.format( year = year,
                                            header_hash = header_hash,
                                            characters = characters,
                                            size = size )
  with open( header_path, 'w', newline = '\n', encoding='utf8' ) as header_file:
    header_file.write( contents )


def Main():
  characters = GetCharacters()
  table_path = os.path.join( DIR_OF_CPP_SOURCES, 'UnicodeTable.h' )
  GenerateUnicodeTable( table_path, characters )


if __name__ == '__main__':
  Main()
