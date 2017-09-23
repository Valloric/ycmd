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

#include <array>
#include <cstring>

namespace YouCompleteMe {

namespace {

const RawCharacter FindCharacter( const char *text ) {
#include "UnicodeTable.inc"

  // Do a binary search on the array of characters to find the raw character
  // corresponding to the text. If no character is found, return the default raw
  // character for that text.
  auto first = characters.begin();
  size_t count = characters.size();

  for ( auto it = first; count > 0; ) {
    size_t step = count / 2;
    it = first + step;
    int cmp = std::strcmp( it->original, text );
    if ( cmp == 0 )
      return *it;
    if ( cmp < 0 ) {
      first = ++it;
      count -= step + 1;
    } else
      count = step;
  }

  return { text, text, text, false, false, false };
}

} // unnamed namespace

Character::Character( const std::string &character )
  : Character( FindCharacter( character.c_str() ) ) {
}


Character::Character( const RawCharacter &character )
  : original_( character.original ),
    uppercase_( character.uppercase ),
    swapped_case_( character.swapped_case ),
    is_letter_( character.is_letter ),
    is_punctuation_( character.is_punctuation ),
    is_uppercase_( character.is_uppercase ) {
}

} // namespace YouCompleteMe
