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
#include "UnicodeTable.h"

namespace YouCompleteMe {

namespace {

ByteSequence ConvertStringToByteSequence( const std::string &character ) {
  ByteSequence byte_sequence;

  for ( uint8_t byte : character ) {
    byte_sequence.push_back( byte );
  }

  return byte_sequence;
};

} // unnamed namespace

Character::Character( const std::string &character ) {
  const RawCharacter raw_character = FindCharacter( character.c_str() );
  if ( raw_character.original ) {
    original_ = ConvertStringToByteSequence( raw_character.original );
    lowercase_ = ConvertStringToByteSequence( raw_character.lowercase );
    uppercase_ = ConvertStringToByteSequence( raw_character.uppercase );
    is_letter_ = raw_character.is_letter;
    is_punctuation_ = raw_character.is_punctuation;
    is_uppercase_ = raw_character.is_uppercase;
  } else {
    original_ = ConvertStringToByteSequence( character );
    lowercase_ = original_;
    uppercase_ = original_;
    is_letter_ = false;
    is_punctuation_ = false;
    is_uppercase_ = false;
  }
}

} // namespace YouCompleteMe
