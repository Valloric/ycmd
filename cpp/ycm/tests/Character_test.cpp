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
#include "CharacterRepository.h"
#include "CodePoint.h"
#include "TestUtils.h"

#include <array>
#include <gtest/gtest.h>
#include <gmock/gmock.h>

using ::testing::TestWithParam;
using ::testing::ValuesIn;

namespace YouCompleteMe {

struct TextCharacterPair {
  const char* text;
  CharacterTuple character_tuple;
};


std::ostream& operator<<( std::ostream& os,
                          const TextCharacterPair &pair ) {
  os << "{ " << PrintToString( pair.text ) << ", "
             << PrintToString( pair.character_tuple ) << " }";
  return os;
}


class CharacterTest : public TestWithParam< TextCharacterPair > {
protected:
  CharacterTest()
    : repo_( CharacterRepository::Instance() ) {
  }

  virtual void SetUp() {
    repo_.ClearCharacters();
    pair_ = GetParam();
  }

  CharacterRepository &repo_;
  const char* text_;
  TextCharacterPair pair_;
};


TEST( CharacterTest, ExceptionThrownWhenLeadingByteInCodePointIsInvalid ) {
  try {
    // Leading byte cannot start with bits '10'.
    Character( "\xaf" );
    FAIL() << "Expected UnicodeDecodeError exception.";
  } catch ( const UnicodeDecodeError &error ) {
    EXPECT_STREQ( error.what(), "Invalid leading byte in code point." );
  } catch ( ... ) {
    FAIL() << "Expected UnicodeDecodeError exception.";
  }
}


TEST( CharacterTest, ExceptionThrownWhenCodePointIsOutOfBound ) {
  try {
    // Leading byte indicates a sequence of three bytes but only two are given.
    Character( "\xe4\xbf" );
    FAIL() << "Expected UnicodeDecodeError exception.";
  } catch ( const UnicodeDecodeError &error ) {
    EXPECT_STREQ( error.what(), "Invalid code point length." );
  } catch ( ... ) {
    FAIL() << "Expected UnicodeDecodeError exception.";
  }
}


TEST_P( CharacterTest, PropertiesAreCorrect ) {
  EXPECT_THAT( Character( pair_.text ),
               IsCharacterWithProperties( pair_.character_tuple ) );
}


const std::array< TextCharacterPair, 13 > tests = { {
  // Musical symbol eighth note (three code points)
  { "𝅘𝅥𝅮", { "𝅘𝅥𝅮", "𝅘𝅥𝅮", "𝅘𝅥𝅮", false, false, false } },

  // Punctuations
  // Fullwidth low line
  { "＿", { "＿", "＿", "＿", false, true, false } },
  // Wavy dash
  { "〰", { "〰", "〰", "〰", false, true, false } },
  // Left floor
  { "⌊", { "⌊", "⌊", "⌊", false, true, false } },
  // Fullwidth right square bracket
  { "］", { "］", "］", "］", false, true, false } },
  { "«", { "«", "«", "«", false, true, false } },
  // Right substitution bracket
  { "⸃", { "⸃", "⸃", "⸃", false, true, false } },
  // Large one dot over two dots punctuation
  { "𐬽", { "𐬽", "𐬽", "𐬽", false, true, false } },

  // Letters
  // Latin capital letter S with dot below and dot above (three code points)
  { "Ṩ", { "Ṩ", "Ṩ", "ṩ", true, false, true } },
  // Greek small letter alpha with psili and varia and ypogegrammeni (four code
  // points)
  { "ᾆ", { "ᾆ", "ἎΙ", "ἎΙ", true, false, false } },
  // Greek capital letter eta with dasia and perispomeni and prosgegrammeni
  // (four code points)
  { "ᾟ", { "ᾟ", "ἯΙ", "ἧΙ", true, false, true } },
  // Hiragana voiced iteration mark (two code points)
  { "ゞ", { "ゞ", "ゞ", "ゞ", true, false, false } },
  // Hebrew letter shin with Dagesh and Shin dot (three code points)
  { "שּׁ", { "שּׁ", "שּׁ", "שּׁ", true, false, false } }
} };


INSTANTIATE_TEST_CASE_P( UnicodeTest, CharacterTest, ValuesIn( tests ) );

} // namespace YouCompleteMe
