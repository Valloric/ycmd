# Copyright (C) 2016 Davit Samvelyan
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

from nose.tools import eq_
from hamcrest import ( assert_that, contains, has_items )

from .clang_handlers_test import Clang_Handlers_test
from ycmd.responses import ( BuildRangeData, Range, Location )
from ycmd.utils import ReadFile
import http.client


class Clang_GetSemanticTokens_test( Clang_Handlers_test ):

  def __init__( self ):
    super( Clang_GetSemanticTokens_test, self ).__init__()
    self._test_file = self._PathToTestFile( 'GetTokens_Clang_test.cc' )


  def setUp( self ):
    super( Clang_GetSemanticTokens_test, self ).setUp()

    self._app.post_json( '/load_extra_conf_file', {
      'filepath': self._PathToTestFile( '.ycm_extra_conf.py' ) } )
    request = {
      'filetype': 'cpp',
      'filepath': self._test_file,
      'event_name': 'FileReadyToParse',
      'contents': ReadFile( self._test_file )
    }
    self._app.post_json( '/event_notification',
                         self._BuildRequest( **request ),
                         expect_errors = False )


  def _BuildTokenData( self, kind, type, sl, sc, el, ec ):
    return {
      'kind': kind,
      'type': type,
      'range': BuildRangeData( Range( Location( sl, sc, self._test_file ),
                                      Location( el, ec, self._test_file ) ) )
    }


  def _RunTest( self, start_line, start_column, end_line, end_column, expect ):
    request = {
      'filetypes': 'cpp',
      'filepath': self._test_file,
      'start_line': start_line,
      'start_column': start_column,
      'end_line': end_line,
      'end_column': end_column,
    }
    response = self._app.post_json( '/semantic_tokens',
                                    self._BuildRequest( **request ),
                                    expect_errors = False )

    eq_( response.status_code, http.client.OK )
    assert_that( response.json, expect )


  def PreprocessingTokens_test( self ):
    self._RunTest( 1, 1, 4, 22,
                   has_items(
                     self._BuildTokenData( 'Punctuation', 'None', 1, 1, 1, 2 ),
                     self._BuildTokenData( 'Identifier',
                                           'PreprocessingDirective',
                                           1, 2, 1, 8 ),
                     self._BuildTokenData( 'Identifier', 'Macro', 1, 9, 1, 11 ),
                     # Literals in preprocessing directives are reported as
                     # Macro definitions by clang (FIX when fixed in clang).
                     self._BuildTokenData( 'Literal', 'Macro', 1, 12, 1, 17 ),
                     self._BuildTokenData( 'Identifier', 'Macro', 2, 9, 2, 15 ),
                     self._BuildTokenData( 'Identifier', 'Macro', 3, 9, 3, 13 ),
                     self._BuildTokenData( 'Identifier', 'Macro',
                                           3, 20, 3, 22 ),
                     self._BuildTokenData( 'Identifier', 'Macro',
                                           3, 25, 3, 31 ),
                     self._BuildTokenData( 'Identifier', 'Macro',
                                           4, 20, 4, 24 ),
                   ) )


  def DeclarationTokens_test( self ):
    self._RunTest( 6, 1, 42, 17,
                   has_items(
                     self._BuildTokenData( 'Identifier', 'Namespace',
                                           6, 11, 6, 13 ),

                     self._BuildTokenData( 'Comment', 'None',
                                           8, 1, 11, 4 ),

                     self._BuildTokenData( 'Identifier', 'TemplateType',
                                           12, 17, 12, 18 ),
                     self._BuildTokenData( 'Identifier', 'Class',
                                           13, 7, 13, 10 ),
                     self._BuildTokenData( 'Identifier', 'Function',
                                           16, 3, 16, 6 ),
                     self._BuildTokenData( 'Identifier', 'TemplateType',
                                           16, 7, 16, 8 ),
                     self._BuildTokenData( 'Identifier', 'Function',
                                           17, 4, 17, 7 ),
                     self._BuildTokenData( 'Identifier', 'Function',
                                           19, 8, 19, 17 ),
                     self._BuildTokenData( 'Identifier', 'TemplateType',
                                           19, 18, 19, 19 ),
                     self._BuildTokenData( 'Identifier', 'FunctionParam',
                                           19, 20, 19, 23 ),
                     self._BuildTokenData( 'Identifier', 'MemberVariable',
                                           20, 5, 20, 6 ),
                     self._BuildTokenData( 'Identifier', 'FunctionParam',
                                           20, 9, 20, 12 ),
                     self._BuildTokenData( 'Identifier', 'TemplateType',
                                           24, 3, 24, 4 ),
                     self._BuildTokenData( 'Identifier', 'MemberVariable',
                                           24, 5, 24, 6 ),

                     self._BuildTokenData( 'Identifier', 'Class',
                                           27, 9, 27, 12 ),
                     self._BuildTokenData( 'Identifier', 'Typedef',
                                           27, 18, 27, 24 ),

                     self._BuildTokenData( 'Identifier', 'Struct',
                                           29, 8, 29, 10 ),

                     self._BuildTokenData( 'Identifier', 'Enum',
                                           31, 6, 31, 8 ),

                     self._BuildTokenData( 'Identifier', 'EnumConstant',
                                           32, 3, 32, 13 ),
                     self._BuildTokenData( 'Identifier', 'EnumConstant',
                                           33, 3, 33, 13 ),

                     self._BuildTokenData( 'Identifier', 'Union',
                                           36, 7, 36, 9 ),
                     self._BuildTokenData( 'Comment', 'None',
                                           36, 10, 36, 25 ),

                   ) )


  def LiteralTokens_test( self ):
    self._RunTest( 48, 1, 51, 24,
                   has_items(
                     self._BuildTokenData( 'Literal', 'Integer',
                                           48, 11, 48, 14 ),
                     self._BuildTokenData( 'Literal', 'Floating',
                                           49, 13, 49, 18 ),
                     self._BuildTokenData( 'Literal', 'Character',
                                           50, 12, 50, 15 ),
                     self._BuildTokenData( 'Literal', 'String',
                                           51, 19, 51, 24 ),
                   ) )


  def DetailedUsageTokens_test( self ):
    self._RunTest( 53, 1, 54, 28,
                   contains(
                     self._BuildTokenData( 'Identifier', 'Namespace',
                                           53, 3, 53, 5 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 5, 53, 7 ),
                     self._BuildTokenData( 'Identifier', 'Typedef',
                                           53, 7, 53, 13 ),
                     self._BuildTokenData( 'Identifier', 'Unsupported',
                                           53, 14, 53, 17 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 18, 53, 19 ),
                     self._BuildTokenData( 'Identifier', 'Namespace',
                                           53, 20, 53, 22 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 22, 53, 24 ),
                     self._BuildTokenData( 'Identifier', 'Typedef',
                                           53, 24, 53, 30 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 30, 53, 31 ),
                     self._BuildTokenData( 'Identifier', 'FunctionParam',
                                           53, 31, 53, 35 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 35, 53, 36 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           53, 36, 53, 37 ),

                     self._BuildTokenData( 'Identifier', 'Namespace',
                                           54, 3, 54, 5 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           54, 5, 54, 7 ),
                     self._BuildTokenData( 'Identifier', 'Enum',
                                           54, 7, 54, 9 ),
                     self._BuildTokenData( 'Identifier', 'Unsupported',
                                           54, 10, 54, 11 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           54, 12, 54, 13 ),
                     self._BuildTokenData( 'Identifier', 'Namespace',
                                           54, 14, 54, 16 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           54, 16, 54, 18 ),
                     self._BuildTokenData( 'Identifier', 'EnumConstant',
                                           54, 18, 54, 28 ),
                     self._BuildTokenData( 'Punctuation', 'None',
                                           54, 28, 54, 29 ),
                   ) )


  def UnicodeTokens_test( self ):
    self._RunTest( 56, 1, 59, 10,
                   has_items(
                     self._BuildTokenData( 'Comment', 'None',
                                           56, 3, 56, 22 ),
                     self._BuildTokenData( 'Identifier', 'Typedef',
                                           57, 18, 57, 24 ),
                     self._BuildTokenData( 'Identifier', 'Typedef',
                                           58, 3, 58, 9 ),
                     self._BuildTokenData( 'Identifier', 'Unsupported',
                                           58, 10, 58, 12 ),
                     self._BuildTokenData( 'Identifier', 'MemberVariable',
                                           59, 6, 59, 7 ),
                   ) )
