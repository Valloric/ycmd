// Copyright (C) 2018 ycmd contributors
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

#include "Character.h"
#include "CodePoint.h"

#include <algorithm>

namespace YouCompleteMe {

namespace {

bool CodePointCompare( const CodePoint *left, const CodePoint *right ) {
  return *left < *right;
}


// Sort the code points according to the Canonical Ordering Algorithm.
// See https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G49591
CodePointSequence CanonicalSort( CodePointSequence code_points ) {
  auto code_point_start = code_points.begin();

  while ( code_point_start != code_points.end() ) {
    if ( ( *code_point_start )->CombiningClass() == 0 ) {
      ++code_point_start;
      continue;
    }

    auto code_point_end = code_point_start + 1;
    while ( code_point_end != code_points.end() &&
            ( *code_point_end )->CombiningClass() != 0 ) {
      ++code_point_end;
    }

    std::sort( code_point_start, code_point_end, CodePointCompare );

    if ( code_point_end == code_points.end() ) {
      break;
    }

    code_point_start = code_point_end + 1;
  }

  return code_points;
}


// Decompose a UTF-8 encoded string into a sequence of code points according to
// Canonical Decomposition. See
// https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G733
CodePointSequence CanonicalDecompose( const std::string &text ) {
  CodePointSequence code_points = BreakIntoCodePoints( text );
  std::string normal;

  for ( const auto &code_point : code_points ) {
    normal.append( code_point->Normal() );
  }

  return CanonicalSort( BreakIntoCodePoints( normal ) );
}

} // unnamed namespace

Character::Character( const std::string &character ) {
  // Normalize the character through NFD (Normalization Form D). See
  // https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G49621
  CodePointSequence code_points = CanonicalDecompose( character );

  auto code_point_pos = code_points.begin();
  if ( code_point_pos == code_points.end() ) {
    return;
  }

  const auto &first_code_point = *code_point_pos;
  is_letter_ = first_code_point->IsLetter();
  is_punctuation_ = first_code_point->IsPunctuation();
  is_uppercase_ = first_code_point->IsUppercase();

  for ( ; code_point_pos != code_points.end(); ++code_point_pos ) {
    const auto &code_point = *code_point_pos;
    normal_.append( code_point->Normal() );
    uppercase_.append( code_point->Uppercase() );
    swapped_case_.append( code_point->SwappedCase() );
  }
}

} // namespace YouCompleteMe
