# Copyright (C) 2015 ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from hamcrest import assert_that
from nose.tools import eq_
import os.path

from ycmd.utils import ReadFile
from ycmd.tests.java import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import BuildRequest, ErrorMatcher


@SharedYcmd
def Subcommands_GetDoc_Method_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'AbstractTestWidget.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 17,
                             column_num = 17,
                             contents = contents,
                             command_arguments = [ 'GetDoc' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'Return runtime debugging info. '
                    'Useful for finding the actual code which is useful.'
  } )


@SharedYcmd
def Subcommands_GetDoc_Class_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 11,
                             column_num = 7,
                             contents = contents,
                             command_arguments = [ 'GetDoc' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'This is the actual code that matters.'
                    ' This concrete implementation is the equivalent'
                    ' of the main function in other languages'
  } )


@SharedYcmd
def Subcommands_GetType_Class_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 11,
                             column_num = 7,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'com.test.TestWidgetImpl'
  } )

@SharedYcmd
def Subcommands_GetType_Constructor_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 14,
                             column_num = 3,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'com.test.TestWidgetImpl.TestWidgetImpl(String info)'
  } )


@SharedYcmd
def Subcommands_GetType_ClassMemberVariable_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 12,
                             column_num = 18,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'String info'
  } )


@SharedYcmd
def Subcommands_GetType_MethodArgument_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 16,
                             column_num = 17,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
    'message': 'String info - '
                     'com.test.TestWidgetImpl.TestWidgetImpl(String)'
  } )

@SharedYcmd
def Subcommands_GetType_MethodVariable_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 15,
                             column_num = 9,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'int a - '
                    'com.test.TestWidgetImpl.TestWidgetImpl(String)'
  } )


@SharedYcmd
def Subcommands_GetType_Method_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'TestWidgetImpl.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 20,
                             column_num = 15,
                             contents = contents,
                             command_arguments = [ 'GetType' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, {
         'message': 'void com.test.TestWidgetImpl.doSomethingVaguelyUseful()'
  } )

# Commented out because of an overlooked corner case
#@SharedYcmd
#def Subcommands_GetType_Class_test( app ):
#  filepath = PathToTestFile( 'simple_eclipse_project',
#                             'src',
#                             'com',
#                             'test',
#                             'TestWidgetImpl.java' )
#  contents = ReadFile( filepath )
#
#  event_data = BuildRequest( filepath = filepath,
#                             filetype = 'java',
#                             line_num = 15,
#                             column_num = 13,
#                             contents = contents,
#                             command_arguments = [ 'GetType' ],
#                             completer_target = 'filetype_default' )
#
#  response = app.post_json( '/run_completer_command', event_data ).json
#
#  eq_( response, {
#    'message': ''
#  } )


@SharedYcmd
def Subcommands_GoToReferences_test( app ):
  filepath = PathToTestFile( 'simple_eclipse_project',
                             'src',
                             'com',
                             'test',
                             'AbstractTestWidget.java' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'java',
                             line_num = 10,
                             column_num = 15,
                             contents = contents,
                             command_arguments = [ 'GoToReferences' ],
                             completer_target = 'filetype_default' )

  response = app.post_json( '/run_completer_command', event_data ).json

  eq_( response, [
         {
           'filepath': PathToTestFile( 'simple_eclipse_project',
                                       'src',
                                       'com',
                                       'test',
                                       'TestFactory.java' ),
           'column_num': 9,
           # 'description': '',
           'line_num': 23
         },
         {
           'filepath': PathToTestFile( 'simple_eclipse_project',
                                       'src',
                                       'com',
                                       'test',
                                       'TestLauncher.java' ),
           'column_num': 7,
           # 'description': '',
           'line_num': 8
         } ] )
