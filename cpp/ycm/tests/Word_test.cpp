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
#include "Word.h"

namespace YouCompleteMe {

TEST( WordTest, ExceptionThrownWhenLeadingByteInCodePointIsInvalid ) {
  try {
    // Leading byte cannot start with bits '10'.
    Word( "\xaf" );
    FAIL() << "Expected UnicodeDecodeError exception.";
  } catch ( const UnicodeDecodeError &error ) {
    EXPECT_STREQ( error.what(), "Invalid leading byte in code point." );
  } catch ( ... ) {
    FAIL() << "Expected UnicodeDecodeError exception.";
  }
}

TEST( WordTest, ExceptionThrownWhenCodePointIsOutOfBound ) {
  try {
    // Leading byte indicates a sequence of three bytes but only two are given.
    Word( "\xe4\xbf" );
    FAIL() << "Expected UnicodeDecodeError exception.";
  } catch ( const UnicodeDecodeError &error ) {
    EXPECT_STREQ( error.what(), "Invalid code point length." );
  } catch ( ... ) {
    FAIL() << "Expected UnicodeDecodeError exception.";
  }
}

TEST( WordTest, MatchesBytes ) {
  Word word( "f𐍈oβaＡaR" );

  EXPECT_TRUE( word.ContainsBytes( Word( "f𐍈oβaＡar" ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "F𐍈oβaａaR" ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "foΒar"    ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "RＡβof"    ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "βfr𐍈ａ"    ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "fβr"      ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "r"        ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( "βββ"      ) ) );
  EXPECT_TRUE( word.ContainsBytes( Word( ""         ) ) );
}

TEST( WordTest, DoesntMatchBytes ) {
  Word word( "Fo𐍈βＡr" );

  EXPECT_FALSE( word.ContainsBytes( Word( "Fo𐍈βＡrε" ) ) );
  EXPECT_FALSE( word.ContainsBytes( Word( "gggg"    ) ) );
  EXPECT_FALSE( word.ContainsBytes( Word( "χ"       ) ) );
  EXPECT_FALSE( word.ContainsBytes( Word( "nfooΒａr" ) ) );
  EXPECT_FALSE( word.ContainsBytes( Word( "Fβrmmm"  ) ) );
}

} // namespace YouCompleteMe
