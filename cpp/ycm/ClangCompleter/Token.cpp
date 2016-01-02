// Copyright (C) 2011, 2012  Google Inc.
//
// This file is part of YouCompleteMe.
//
// YouCompleteMe is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// YouCompleteMe is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

#include "Token.h"

namespace YouCompleteMe {

namespace {

Token::Kind CursorToTokenKind( CXCursor cursor ) {
  CXCursorKind kind = clang_getCursorKind( cursor );
  switch (kind) {
    case CXCursor_Namespace:
    case CXCursor_NamespaceAlias:
    case CXCursor_NamespaceRef:
      return Token::NAMESPACE;

    case CXCursor_ClassDecl:
    case CXCursor_ClassTemplate:
      return Token::CLASS;

    case CXCursor_StructDecl:
      return Token::STRUCT;

    case CXCursor_UnionDecl:
      return Token::UNION;

    case CXCursor_TypedefDecl:
      return Token::TYPEDEF;

    case CXCursor_EnumDecl:
      return Token::ENUM;

    case CXCursor_EnumConstantDecl:
      return Token::ENUM_CONSTANT;

    //case CXCursor_MacroDefinition: // Definition is easily recognized by a regexp.
    //case CXCursor_MacroExpansion: // Currently is the same as CXCursor_MacroInstantiation
    case CXCursor_MacroInstantiation:
      return Token::MACRO;

    case CXCursor_FunctionDecl:
    case CXCursor_CXXMethod:
      return Token::FUNCTION;

    case CXCursor_ParmDecl:
      return Token::FUNCTION_PARAM;

    // When we have a type reference we need to do one more step
    // to find out whether it is referencing class, enum, ... or typedef.
    case CXCursor_TypeRef:
    case CXCursor_DeclRefExpr:
    case CXCursor_MemberRefExpr:
    case CXCursor_TemplateRef:
    {
      CXCursor ref = clang_getCursorReferenced( cursor );
      if ( clang_Cursor_isNull( ref ) ) {
        return Token::UNSUPPORTED;
      } else {
        return CursorToTokenKind( ref );
      }
    }

    default:
      return Token::UNSUPPORTED;
  }
}

} // unnamed namespace

Token::Token()
  : kind_( UNSUPPORTED ) {
}

Token::Token( const CXSourceRange& tokenRange, const CXCursor& cursor ) {

  kind_ = CursorToTokenKind( cursor );
  if ( kind_ == UNSUPPORTED ) {
    return;
  }

  location_extent_ = Range( tokenRange );
  // There shouldn't exist any multiline Token, except for multiline strings,
  // which is unsupported at the moment, but better be safe then sorry.
  if ( location_extent_.start_.line_number_ !=
         location_extent_.end_.line_number_ ) {
    kind_ = UNSUPPORTED;
  }
}

bool Token::operator== ( const Token& other ) const {
  return kind_ == other.kind_ &&
         location_extent_ == other.location_extent_;
}

} // YouCompleteMe
