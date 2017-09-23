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

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "Character.h"

using ::testing::AllOf;
using ::testing::ContainerEq;
using ::testing::ElementsAre;
using ::testing::Not;
using ::testing::Property;

namespace YouCompleteMe {

// NOTE: we don't test Unicode characters stored on multiple code points since
// we don't support them. We could handle them but they are so rare that this
// doesn't seem worth the extra complexity.

TEST( CharacterTest, InvalidCharacter ) {
  // NOTE: we don't validate characters as this would impact performance and
  // wouldn't be particularly useful.

  // Leading byte indicates a sequence of two bytes but four are given.
  EXPECT_THAT( Character( "\xce\x9a\xb4\xae" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xce', '\x9a', '\xb4', '\xae' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xce', '\x9a', '\xb4', '\xae' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xce', '\x9a', '\xb4', '\xae' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );
}

TEST( CharacterTest, LetterCharacter ) {
  // One byte characters

  // Lowercase
  EXPECT_THAT( Character( "r" ), AllOf(
    Property( &Character::Original,      ElementsAre( '\x72' ) ),
    Property( &Character::Lowercase,     ElementsAre( '\x72' ) ),
    Property( &Character::Uppercase,     ElementsAre( '\x52' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Uppercase
  EXPECT_THAT( Character( "R" ), AllOf(
    Property( &Character::Original,      ElementsAre( '\x52' ) ),
    Property( &Character::Lowercase,     ElementsAre( '\x72' ) ),
    Property( &Character::Uppercase,     ElementsAre( '\x52' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  EXPECT_TRUE( Character( "r" ).EqualsIgnoreCase( Character( "R" ) ) );
  EXPECT_TRUE( Character( "R" ).EqualsIgnoreCase( Character( "r" ) ) );

  // NOTE: there are no Unicode letters coded with one byte (i.e. ASCII letters)
  // without a lowercase or uppercase version.

  // Two bytes characters

  // Lowercase
  EXPECT_THAT( Character( "é" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xc3', '\xa9' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc3', '\xa9' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc3', '\x89' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Uppercase
  EXPECT_THAT( Character( "É" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xc3', '\x89' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc3', '\xa9' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc3', '\x89' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  EXPECT_TRUE( Character( "é" ).EqualsIgnoreCase( Character( "É" ) ) );
  EXPECT_TRUE( Character( "É" ).EqualsIgnoreCase( Character( "é" ) ) );

  // No case
  EXPECT_THAT( Character( "ĸ" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xc4', '\xb8' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc4', '\xb8' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc4', '\xb8' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Three bytes characters

  // NOTE: the uppercase or lowercase version of a Unicode letter is not
  // necessarily coded with the same number of bytes.

  // Lowercase
  EXPECT_THAT( Character( "ⱥ" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xe2', '\xb1', '\xa5' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xe2', '\xb1', '\xa5' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc8', '\xba' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Uppercase
  EXPECT_THAT( Character( "Ɐ" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xe2', '\xb1', '\xaf' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc9', '\x90' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xe2', '\xb1', '\xaf' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  EXPECT_TRUE( Character( "ⱥ" ).EqualsIgnoreCase( Character( "Ⱥ" ) ) );
  EXPECT_TRUE( Character( "Ⱥ" ).EqualsIgnoreCase( Character( "ⱥ" ) ) );
  EXPECT_TRUE( Character( "Ɐ" ).EqualsIgnoreCase( Character( "ɐ" ) ) );
  EXPECT_TRUE( Character( "ɐ" ).EqualsIgnoreCase( Character( "Ɐ" ) ) );

  // No case
  EXPECT_THAT( Character( "の" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xe3', '\x81', '\xae' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xe3', '\x81', '\xae' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xe3', '\x81', '\xae' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Four bytes characters

  // Lowercase
  EXPECT_THAT( Character( "𐐫" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xf0', '\x90', '\x90', '\xab' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xf0', '\x90', '\x90', '\xab' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xf0', '\x90', '\x90', '\x83' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Uppercase
  EXPECT_THAT( Character( "𐐃" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xf0', '\x90', '\x90', '\x83' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xf0', '\x90', '\x90', '\xab' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xf0', '\x90', '\x90', '\x83' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  EXPECT_TRUE( Character( "𐐫" ).EqualsIgnoreCase( Character( "𐐃" ) ) );
  EXPECT_TRUE( Character( "𐐃" ).EqualsIgnoreCase( Character( "𐐫" ) ) );

  // No case
  EXPECT_THAT( Character( "𐰬" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xf0', '\x90', '\xb0', '\xac' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xf0', '\x90', '\xb0', '\xac' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xf0', '\x90', '\xb0', '\xac' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );
}

TEST( CharacterTest, PunctuationCharacter ) {
  // One byte character
  EXPECT_THAT( Character( "'" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\x27' ) ),
    Property( &Character::Lowercase, ElementsAre( '\x27' ) ),
    Property( &Character::Uppercase, ElementsAre( '\x27' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, true ),
    Property( &Character::IsUppercase,   false ) ) );

  // Two bytes character
  EXPECT_THAT( Character( "»" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xc2', '\xbb' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc2', '\xbb' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc2', '\xbb' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, true ),
    Property( &Character::IsUppercase,   false ) ) );

  // Three bytes character
  EXPECT_THAT( Character( "•" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xe2', '\x80', '\xa2' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xe2', '\x80', '\xa2' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xe2', '\x80', '\xa2' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, true ),
    Property( &Character::IsUppercase,   false ) ) );

  // Four bytes character
  EXPECT_THAT( Character( "𐬿" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xf0', '\x90', '\xac', '\xbf' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xf0', '\x90', '\xac', '\xbf' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xf0', '\x90', '\xac', '\xbf' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, true ),
    Property( &Character::IsUppercase,   false ) ) );
}

TEST( CharacterTest, OtherCharacter ) {
  // One byte character
  EXPECT_THAT( Character( "=" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\x3d' ) ),
    Property( &Character::Lowercase, ElementsAre( '\x3d' ) ),
    Property( &Character::Uppercase, ElementsAre( '\x3d' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Two bytes character
  EXPECT_THAT( Character( "©" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xc2', '\xa9' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xc2', '\xa9' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xc2', '\xa9' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Three bytes character
  EXPECT_THAT( Character( "∅" ), AllOf(
    Property( &Character::Original,  ElementsAre( '\xe2', '\x88', '\x85' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xe2', '\x88', '\x85' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xe2', '\x88', '\x85' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );

  // Four bytes character
  EXPECT_THAT( Character( "𝛁" ), AllOf(
    Property( &Character::Original,
              ElementsAre( '\xf0', '\x9d', '\x9b', '\x81' ) ),
    Property( &Character::Lowercase,
              ElementsAre( '\xf0', '\x9d', '\x9b', '\x81' ) ),
    Property( &Character::Uppercase,
              ElementsAre( '\xf0', '\x9d', '\x9b', '\x81' ) ),
    Property( &Character::IsLetter,      false ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   false ) ) );
}

TEST( CharacterTest, SameCharacterDifferentCodePoints ) {
  // The Greek capital letter Omega
  Character omega( "Ω" );
  EXPECT_THAT( omega, AllOf(
    Property( &Character::Original,  ElementsAre( '\xce', '\xa9' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xcf', '\x89' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xce', '\xa9' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  // The ohm symbol
  Character ohm( "Ω" );
  EXPECT_THAT( ohm, AllOf(
    Property( &Character::Original,  ElementsAre( '\xe2', '\x84', '\xa6' ) ),
    Property( &Character::Lowercase, ElementsAre( '\xcf', '\x89' ) ),
    Property( &Character::Uppercase, ElementsAre( '\xe2', '\x84', '\xa6' ) ),
    Property( &Character::IsLetter,      true ),
    Property( &Character::IsPunctuation, false ),
    Property( &Character::IsUppercase,   true ) ) );

  // FIXME: two code points can represent the same character. We incorrectly
  // consider them as two distinct characters.
  EXPECT_FALSE( omega == ohm );
}

} // namespace YouCompleteMe
