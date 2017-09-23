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
#include "exceptions.h"
#include "Word.h"

namespace YouCompleteMe {

TEST( WordTest, ExceptionThrownWhenLeadingByteInCodePointIsInvalid ) {
  // Leading byte cannot start with bits '10'.
  EXPECT_THROW( Word( "\xaf" ), UnicodeDecodeError );
}

TEST( WordTest, ExceptionThrownWhenComputedCodePointWidthIsOutOfBound ) {
  // Leading byte indicates a sequence of three bytes but only two are given.
  EXPECT_THROW( Word( "\xe4\xbf" ), UnicodeDecodeError );
}

TEST( WordTest, MatchesBytes ) {
  Word word( "f𐍈oβaＡaR" );

  EXPECT_TRUE( word.MatchesBytes( Word( "f𐍈oβaＡar" ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "F𐍈oβaａaR" ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "foΒar"    ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "RＡβof"    ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "βfr𐍈ａ"    ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "fβr"      ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "r"        ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( "βββ"      ) ) );
  EXPECT_TRUE( word.MatchesBytes( Word( ""         ) ) );
}

TEST( WordTest, DoesntMatchBytes ) {
  Word word( "Fo𐍈βＡr" );

  EXPECT_FALSE( word.MatchesBytes( Word( "Fo𐍈βＡrε" ) ) );
  EXPECT_FALSE( word.MatchesBytes( Word( "gggg"    ) ) );
  EXPECT_FALSE( word.MatchesBytes( Word( "χ"       ) ) );
  EXPECT_FALSE( word.MatchesBytes( Word( "nfooΒａr" ) ) );
  EXPECT_FALSE( word.MatchesBytes( Word( "Fβrmmm"  ) ) );
}

} // namespace YouCompleteMe
