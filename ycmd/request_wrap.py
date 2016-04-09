# Copyright (C) 2014 Google Inc.
# encoding: utf8
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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycmd.utils import ( ByteOffsetToCodepointOffset,
                         CodepointOffsetToByteOffset,
                         ToUnicode,
                         ToBytes )
from ycmd.identifier_utils import StartOfLongestIdentifierEndingAtIndex
from ycmd.request_validation import EnsureRequestValid

import logging
_logger = logging.getLogger( __name__ )


# TODO: Change the custom computed (and other) keys to be actual properties on
# the object.
class RequestWrap( object ):
  def __init__( self, request, validate = True ):
    if validate:
      EnsureRequestValid( request )
    self._request = request
    self._computed_key = {
      # Unicode string representation of the current line
      'line_value': self._CurrentLine,

      # The calculated start column, as a codepoint offset into the
      # unicode string line_value
      'start_codepoint': self.CompletionStartCodepoint,

      # The 'column_num' as a unicode codepoint offset
      'column_codepoint': (lambda:
        ByteOffsetToCodepointOffset( self[ 'line_bytes' ],
                                     self[ 'column_num' ] ) ),

      # Bytes string representation of the current line
      'line_bytes': lambda: ToBytes( self[ 'line_value' ] ),

      # The calculated start column, as a byte offset into the UTF-8 encoded
      # bytes returned by line_bytes
      'start_column': self.CompletionStartColumn,

      # Note: column_num is the byte offset into the UTF-8 encoded bytes
      # returned by line_bytes

      # unicode string representation of the 'query' after the beginning
      # of the identifier to be completed
      'query': self._Query,

      'filetypes': self._Filetypes,
    }
    self._cached_computed = {}


  def __getitem__( self, key ):
    if key in self._cached_computed:
      return self._cached_computed[ key ]
    if key in self._computed_key:
      value = self._computed_key[ key ]()
      self._cached_computed[ key ] = value
      return value
    return self._request[ key ]


  def __contains__( self, key ):
    return key in self._computed_key or key in self._request


  def get( self, key, default = None ):
    try:
      return self[ key ]
    except KeyError:
      return default


  def _CurrentLine( self ):
    current_file = self._request[ 'filepath' ]
    contents = self._request[ 'file_data' ][ current_file ][ 'contents' ]

    return contents.split( '\n' )[ self._request[ 'line_num' ] - 1 ]


  def CompletionStartColumn( self ):
    try:
      filetype = self[ 'filetypes' ][ 0 ]
    except (KeyError, IndexError):
      filetype = None
    return CompletionStartColumn( self[ 'line_value' ],
                                  self[ 'column_num' ],
                                  filetype )


  def CompletionStartCodepoint( self ):
    try:
      filetype = self[ 'filetypes' ][ 0 ]
    except (KeyError, IndexError):
      filetype = None
    return CompletionStartCodepoint( self[ 'line_value' ],
                                     self[ 'column_num' ],
                                     filetype )


  def _Query( self ):
    query = ToUnicode( self[ 'line_bytes' ][
             self[ 'start_column' ] - 1 : self[ 'column_num' ] - 1 ] )

    _logger.debug( 'Query for line /{0}/ is /{1}/'.format( self[ 'line_value' ],
                                                           query ) )

    return query


  def _Filetypes( self ):
    path = self[ 'filepath' ]
    return self[ 'file_data' ][ path ][ 'filetypes' ]


def CompletionStartColumn( line_value, column_num, filetype ):
  """Returns the 1-based byte index where the completion query should start.
  So if the user enters:
    foo.bar^
  with the cursor being at the location of the caret (so the character *AFTER*
  'r'), then the starting column would be the index of the letter 'b'.

  NOTE: if the line contains multi-byte characters, then the result is not
  the 'character' index (see CompletionStartCodepoint for that), and therfore
  is is not safe to perform any character-relevant arithmetic on the result
  of this method"""
  return CodepointOffsetToByteOffset(
      ToUnicode( line_value ),
      CompletionStartCodepoint( line_value, column_num, filetype ) )


def CompletionStartCodepoint( line_value, column_num, filetype ):
  """Returns the 1-based codepoint index where the completion query should
  start.  So if the user enters:
    ƒøø.∫å®^
  with the cursor being at the location of the caret (so the character *AFTER*
  '®'), then the starting column would be the index of the character '∫'
  (i.e. 5, not its byte index)."""

  # NOTE: column_num and other numbers on the wire are byte indices, but we need
  # to walk codepoints for identifier checks.
  codepoint_column_num = ByteOffsetToCodepointOffset( line_value, column_num )

  unicode_line_value = ToUnicode( line_value )
  # -1 and then +1 to account for difference betwen 0-based and 1-based
  # indices/columns
  codepoint_start_column = StartOfLongestIdentifierEndingAtIndex(
      unicode_line_value, codepoint_column_num - 1, filetype ) + 1

  return codepoint_start_column
