# Copyright (C) 2016 ycmd contributors
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

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from .cs_handlers_test import Cs_Handlers_test
from nose.tools import ok_
from ycmd.utils import ReadFile
import os.path
import re


class Cs_Isolated_test( Cs_Handlers_test ):

  def setUp( self ):
    self._SetUpApp()
    self._app.post_json(
      '/ignore_extra_conf_file',
      { 'filepath': self._PathToTestFile( '.ycm_extra_conf.py' ) } )


  def Subcommand_StopServer_NoErrorIfNotStarted_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    self._StopOmniSharpServer( filepath )
    # Success = no raise


  def Subcommand_StopServer_KeepLogFiles_test( self ):
    yield self._StopServer_KeepLogFiles, True
    yield self._StopServer_KeepLogFiles, False


  def _StopServer_KeepLogFiles( self, keeping_log_files ):
    with self.UserOption( 'server_keep_logfiles', keeping_log_files ):
      self._app.post_json(
        '/ignore_extra_conf_file',
        { 'filepath': self._PathToTestFile( '.ycm_extra_conf.py' ) } )
      filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
      contents = ReadFile( filepath )
      event_data = self._BuildRequest( filepath = filepath,
                                       filetype = 'cs',
                                       contents = contents,
                                       event_name = 'FileReadyToParse' )

      self._app.post_json( '/event_notification', event_data )
      self._WaitUntilOmniSharpServerReady( filepath )

      event_data = self._BuildRequest( filetype = 'cs', filepath = filepath )

      debuginfo = self._app.post_json( '/debug_info', event_data ).json

      log_files_match = re.search( "^OmniSharp logfiles:\n(.*)\n(.*)",
                                   debuginfo,
                                   re.MULTILINE )
      stdout_logfiles_location = log_files_match.group( 1 )
      stderr_logfiles_location = log_files_match.group( 2 )

      try:
        ok_( os.path.exists(stdout_logfiles_location ),
             "Logfile should exist at {0}".format( stdout_logfiles_location ) )
        ok_( os.path.exists( stderr_logfiles_location ),
             "Logfile should exist at {0}".format( stderr_logfiles_location ) )
      finally:
        self._StopOmniSharpServer( filepath )

      if keeping_log_files:
        ok_( os.path.exists( stdout_logfiles_location ),
             "Logfile should still exist at "
             "{0}".format( stdout_logfiles_location ) )
        ok_( os.path.exists( stderr_logfiles_location ),
             "Logfile should still exist at "
             "{0}".format( stderr_logfiles_location ) )
      else:
        ok_( not os.path.exists( stdout_logfiles_location ),
             "Logfile should no longer exist at "
             "{0}".format( stdout_logfiles_location ) )
        ok_( not os.path.exists( stderr_logfiles_location ),
             "Logfile should no longer exist at "
             "{0}".format( stderr_logfiles_location ) )
