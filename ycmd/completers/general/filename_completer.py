# Copyright (C) 2013-2018 ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import os

from ycmd.completers.completer import Completer
from ycmd.utils import ( ExpandVariablesInPath,
                         GetCurrentDirectory,
                         GetModificationTime,
                         ListDirectory,
                         OnWindows,
                         re,
                         ToUnicode )
from ycmd import responses

FILE = 1
DIR = 2
# This mapping is also used for the #include completion.
# We have option 3, because some entries could simultaneously be
# both a file and a directory.
EXTRA_INFO_MAP = { FILE : '[File]', DIR : '[Dir]', 3 : '[File&Dir]' }

PATH_SEPARATORS_PATTERN = r'([{seps}][^{seps}]*|[{seps}]$)'

HEAD_PATH_PATTERN_UNIX = '\.{1,2}|~|\$[^$]+'
HEAD_PATH_PATTERN_WINDOWS = '[A-Za-z]:|\.{1,2}|~|\$[^$]+|%[^%]+%'


class FilenameCompleter( Completer ):
  """
  General completer that provides filename and filepath completions.
  """

  def __init__( self, user_options ):
    super( FilenameCompleter, self ).__init__( user_options )

    if OnWindows():
      self._path_separators = r'/\\'
      self._head_path_pattern = HEAD_PATH_PATTERN_WINDOWS
    else:
      self._path_separators = '/'
      self._head_path_pattern = HEAD_PATH_PATTERN_UNIX
    print( PATH_SEPARATORS_PATTERN.format( seps = self._path_separators ) )
    self._path_separators_regex = re.compile(
      PATH_SEPARATORS_PATTERN.format( seps = self._path_separators ) )
    self._head_path_for_directory = {}
    self._candidates_for_directory = {}


  def CurrentFiletypeCompletionDisabled( self, request_data ):
    disabled_filetypes = self.user_options[ 'filepath_blacklist' ]
    filetypes = request_data[ 'filetypes' ]
    return ( '*' in disabled_filetypes or
             any( x in disabled_filetypes for x in filetypes ) )


  def GetWorkingDirectory( self, request_data ):
    if self.user_options[ 'filepath_completion_use_working_dir' ]:
      # Return paths relative to the working directory of the client, if
      # supplied, otherwise relative to the current working directory of this
      # process.
      return request_data.get( 'working_dir' ) or GetCurrentDirectory()
    # Return paths relative to the file.
    return os.path.dirname( request_data[ 'filepath' ] )


  def GetCompiledHeadRegexForDirectory( self, directory ):
    mtime = GetModificationTime( directory )

    try:
      head_regex = self._head_path_for_directory[ directory ]
      if mtime and mtime <= head_regex[ 'mtime' ]:
        return head_regex[ 'regex' ]
    except KeyError:
      pass

    current_paths = ListDirectory( directory )
    current_paths_pattern = '|'.join(
      [ re.escape( path ) for path in current_paths ] )
    head_pattern = ( '(' + self._head_path_pattern + '|'
                         + current_paths_pattern + ')$' )
    head_regex = re.compile( head_pattern )
    if mtime:
      self._head_path_for_directory[ directory ] = {
        'regex': head_regex,
        'mtime': mtime
      }
    return head_regex


  def DetectPath( self, request_data ):
    current_line = request_data[ 'prefix' ]
    matches = list( self._path_separators_regex.finditer( current_line ) )
    if not matches:
      return None, None

    working_dir = self.GetWorkingDirectory( request_data )

    head_regex = self.GetCompiledHeadRegexForDirectory( working_dir )

    last_match = matches[ -1 ]
    last_match_start = last_match.start( 1 )

    for match in matches:
      head_match = head_regex.search( current_line[ : match.start() ] )
      if head_match:
        path = current_line[ head_match.start( 1 ) : last_match_start ]
        path = ExpandVariablesInPath( path + os.path.sep )
        if not os.path.isabs( path ):
          path = os.path.join( working_dir, path )
        if os.path.exists( path ):
          return path, last_match_start + 2

      # Path doesn't start with ".", "..", "~", an environment variable, or one
      # of the current directories. It also doesn't start with a drive letter on
      # Windows. Assume that it starts with "/" (or "\" on Windows).
      path = current_line[ match.start() : last_match_start ]
      if path.strip( self._path_separators ):
        path = ExpandVariablesInPath( path + os.path.sep )
        if os.path.exists( path ):
          return path, last_match_start + 2

    # Path is exactly "/" (or "\" on Windows). Only complete if there are no
    # other separators before on the line. This prevents always completing the
    # root directory if nothing is matched.
    # TODO: completion on a single "/" or "\" is not really desirable in
    # languages where such characters are part of special constructs like
    # comments in C/C++ or closing tags in HTML. This behavior could be improved
    # by using rules that depend on the filetype.
    if len( matches ) == 1:
      return os.path.sep, last_match_start + 2

    return None, None


  def ShouldUseNow( self, request_data ):
    if self.CurrentFiletypeCompletionDisabled( request_data ):
      return False

    return bool( self.DetectPath( request_data )[ 0 ] )


  def SupportedFiletypes( self ):
    return []


  def GetCandidatesForDirectory( self, directory ):
    mtime = GetModificationTime( directory )

    try:
      candidates = self._candidates_for_directory[ directory ]
      if mtime and mtime <= candidates[ 'mtime' ]:
        return candidates[ 'candidates' ]
    except KeyError:
      pass

    candidates = _GeneratePathCompletionCandidates( directory )
    if mtime:
      self._candidates_for_directory[ directory ] = {
        'candidates': candidates,
        'mtime': mtime
      }
    return candidates


  def ComputeCandidates( self, request_data ):
    if not self.ShouldUseNow( request_data ):
      return []

    # Calling this function seems inefficient when it's already been called in
    # ShouldUseNow for that request but its execution time is so low once the
    # head regex is cached that it doesn't matter.
    directory, start_codepoint = self.DetectPath( request_data )

    request_data[ 'start_codepoint' ] = start_codepoint

    candidates = self.GetCandidatesForDirectory( directory )
    return self.FilterAndSortCandidates( candidates, request_data[ 'query' ] )


def _GeneratePathCompletionCandidates( path_dir ):
  completions = []

  unicode_path = ToUnicode( path_dir )

  for rel_path in ListDirectory( unicode_path ):
    absolute_path = os.path.join( unicode_path, rel_path )
    path_type = GetPathTypeName( GetPathType( absolute_path ) )
    completions.append(
      responses.BuildCompletionData( rel_path, path_type ) )

  return completions


def GetPathType( path ):
  return DIR if os.path.isdir( path ) else FILE


def GetPathTypeName( path_type ):
  return EXTRA_INFO_MAP[ path_type ]
