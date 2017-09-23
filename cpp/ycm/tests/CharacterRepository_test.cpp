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
#include "CharacterRepository.h"

using ::testing::ElementsAre;
using ::testing::Pointee;
using ::testing::Property;
using ::testing::UnorderedElementsAre;

namespace YouCompleteMe {

class CharacterRepositoryTest : public ::testing::Test {
protected:
  CharacterRepositoryTest()
    : repo_( CharacterRepository::Instance() ) {
  }

  virtual void SetUp() {
    repo_.ClearCharacters();
  }

  CharacterRepository &repo_;
};


TEST_F( CharacterRepositoryTest, GetCharacters ) {
  std::vector< std::string > characters = { "α", "ω" };

  CharacterSequence character_objects = repo_.GetCharacters( characters );

  EXPECT_THAT( repo_.NumStoredCharacters(), 2 );
  EXPECT_THAT( character_objects, UnorderedElementsAre(
    Pointee( Property( &Character::Original, ElementsAre( '\xce', '\xb1' ) ) ),
    Pointee( Property( &Character::Original, ElementsAre( '\xcf', '\x89' ) ) )
  ) );
}

} // namespace YouCompleteMe
