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

#include <string>
#include <vector>

namespace YouCompleteMe {

// This class represents a UTF-8 character. It takes a UTF-8 encoded string
// corresponding to a grapheme cluster (see
// https://www.unicode.org/glossary/#grapheme_cluster), normalize it through NFD
// (see https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G49621), and
// compute the uppercase and the swapped case versions of the normalized
// character. It also holds some properties like if the character is a letter or
// a punctuation, and if it is uppercase.
class Character {
public:
  YCM_EXPORT explicit Character( const std::string &character );
  // Make class noncopyable
  Character( const Character& ) = delete;
  Character& operator=( const Character& ) = delete;

  inline std::string Normal() const {
    return normal_;
  }

  inline std::string Uppercase() const {
    return uppercase_;
  }

  inline std::string SwappedCase() const {
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
    return normal_ == other.normal_;
  };

  inline bool EqualsIgnoreCase( const Character &other ) const {
    return uppercase_ == other.uppercase_;
  };

private:
  std::string normal_;
  std::string uppercase_;
  std::string swapped_case_;
  bool is_letter_;
  bool is_punctuation_;
  bool is_uppercase_;
};


using CharacterSequence = std::vector< const Character * >;

} // namespace YouCompleteMe

#endif /* end of include guard: CHARACTER_H_YTIET2HZ */
