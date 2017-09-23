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

#include "CharacterRepository.h"
#include "Word.h"

namespace YouCompleteMe {

namespace {

int GetCodePointLength( uint8_t leading_byte ) {
  // 0xxxxxxx
  if ( ( leading_byte & 0x80 ) == 0x00 ) {
    return 1;
  }
  // 110xxxxx
  if ( ( leading_byte & 0xe0 ) == 0xc0 ) {
    return 2;
  }
  // 1110xxxx
  if ( ( leading_byte & 0xf0 ) == 0xe0 ) {
    return 3;
  }
  // 11110xxx
  if ( ( leading_byte & 0xf8 ) == 0xf0 ) {
    return 4;
  }
  throw UnicodeDecodeError( "Invalid leading byte in code point." );
}

} // unnamed namespace


void Word::ComputeCharacters() {
  // NOTE: we assume that all Unicode characters hold on a code point. This
  // isn't actually true but characters encoded on multiple code points are so
  // rare (especially in programming) that it's not really worth the complexity
  // to handle them.
  // NOTE: for efficiency, we don't check if the number of continuation bytes
  // and the bytes themselves are valid (they must start with bits '10').
  std::vector< std::string > characters;
  for ( auto iter = text_.begin(); iter != text_.end(); ) {
    int length = GetCodePointLength( *iter );
    if ( text_.end() - iter < length ) {
      throw UnicodeDecodeError( "Invalid code point length." );
    }
    characters.push_back( std::string( iter, iter + length ) );
    iter += length;
  }

  characters_ = CharacterRepository::Instance().GetCharacters( characters );
}


void Word::ComputeBytesPresent() {
  for ( const auto &character : characters_ ) {
    for ( uint8_t byte : character->Uppercase() ) {
      bytes_present_.set( byte );
    }
  }
}


Word::Word( const std::string &text )
  : text_( text ) {
  ComputeCharacters();
  ComputeBytesPresent();
}

} // namespace YouCompleteMe
