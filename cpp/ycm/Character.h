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

#ifndef CHARACTER_H_YTIET2HZ
#define CHARACTER_H_YTIET2HZ

// This header is required on MSVC 12 for the uint8_t type.
#include <cstdint>
#include <string>
#include <vector>

namespace YouCompleteMe {

using ByteSequence = std::vector< uint8_t >;

// This class represents an abstract character. It takes a UTF-8 encoded string
// corresponding to a character, converts it to a sequence of bytes and compute
// the lowercase and uppercase versions of that sequence using a Unicode table.
// It also holds some properties like if the character is a letter or a
// punctuation, and if it is uppercase.
class Character {
public:
  YCM_EXPORT Character( const std::string &character );
  // Make class noncopyable
  Character( const Character& ) = delete;
  Character& operator=( const Character& ) = delete;

  inline ByteSequence Original() const {
    return original_;
  }

  inline ByteSequence Uppercase() const {
    return uppercase_;
  }

  inline ByteSequence SwappedCase() const {
    return swapped_case_;
  }

  inline bool IsLetter() const {
    return is_letter_;
  }

  inline bool IsPunctuation() const {
    return is_punctuation_;
  }

  inline bool IsUppercase() const {
    return is_uppercase_;
  }

  inline bool operator== ( const Character &other ) const {
    return original_ == other.original_;
  };

  inline bool EqualsIgnoreCase( const Character &other ) const {
    return uppercase_ == other.uppercase_;
  };

private:
  ByteSequence original_;
  ByteSequence uppercase_;
  ByteSequence swapped_case_;
  bool is_letter_;
  bool is_punctuation_;
  bool is_uppercase_;
};


using CharacterSequence = std::vector< const Character * >;

} // namespace YouCompleteMe

#endif /* end of include guard: CHARACTER_H_YTIET2HZ */
