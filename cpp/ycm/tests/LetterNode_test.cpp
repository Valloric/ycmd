// Copyright (C) 2016 ycmd contributors
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
#include "LetterNode.h"

namespace YouCompleteMe {

using ::testing::AllOf;
using ::testing::ElementsAre;
using ::testing::IsNull;
using ::testing::Property;

TEST( LetterNode, AsciiText ) {
  LetterNode *node = new LetterNode( "ascIi_texT" );
  EXPECT_THAT( *node,
    AllOf( Property( &LetterNode::Index, -1 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) );

  const std::list< LetterNode *> *list = node->NodeListForLetter( 'i' );
  EXPECT_THAT( *list, ElementsAre(
    AllOf( Property( &LetterNode::Index, 3 ),
           Property( &LetterNode::LetterIsUppercase, true ) ),
    AllOf( Property( &LetterNode::Index, 4 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) ) );

  node = list->front();
  EXPECT_THAT( *node,
    AllOf( Property( &LetterNode::Index, 3 ),
           Property( &LetterNode::LetterIsUppercase, true ) ) );

  list = node->NodeListForLetter( 'i' );
  EXPECT_THAT( *list, ElementsAre(
    AllOf( Property( &LetterNode::Index, 4 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) ) );

  list = node->NodeListForLetter( 't' );
  EXPECT_THAT( *list, ElementsAre(
    AllOf( Property( &LetterNode::Index, 6 ),
           Property( &LetterNode::LetterIsUppercase, false ) ),
    AllOf( Property( &LetterNode::Index, 9 ),
           Property( &LetterNode::LetterIsUppercase, true ) ) ) );

  list = node->NodeListForLetter( 'c' );
  EXPECT_THAT( list, IsNull() );
}


TEST( LetterNode, UnicodeText ) {
  LetterNode *node = new LetterNode( "unicød€" );
  EXPECT_THAT( *node,
    AllOf( Property( &LetterNode::Index, -1 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) );

  const std::list< LetterNode *> *list = node->NodeListForLetter( 'c' );
  EXPECT_THAT( *list, ElementsAre(
    AllOf( Property( &LetterNode::Index, 3 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) ) );

  node = list->front();

  // ø character (\xc3\xb8 in UTF-8) is ignored.
  list = node->NodeListForLetter( '\xc3' );
  EXPECT_THAT( list, IsNull() );
  list = node->NodeListForLetter( '\xb8' );
  EXPECT_THAT( list, IsNull() );

  list = node->NodeListForLetter( 'd' );
  EXPECT_THAT( *list, ElementsAre(
    AllOf( Property( &LetterNode::Index, 6 ),
           Property( &LetterNode::LetterIsUppercase, false ) ) ) );

  // € character (\xe2\x82\xac in UTF-8) is ignored.
  list = node->NodeListForLetter( '\xe2' );
  EXPECT_THAT( list, IsNull() );
  list = node->NodeListForLetter( '\x82' );
  EXPECT_THAT( list, IsNull() );
  list = node->NodeListForLetter( '\xac' );
  EXPECT_THAT( list, IsNull() );
}

} // namespace YouCompleteMe
