// Copyright (C) 2011, 2012 Google Inc.
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

#include "IdentifierUtils.h"
#include "TestUtils.h"
#include "IdentifierDatabase.h"

#include <gtest/gtest.h>
#include <gmock/gmock.h>

namespace YouCompleteMe {

using ::testing::ElementsAre;
using ::testing::ContainerEq;
using ::testing::IsEmpty;
using ::testing::WhenSorted;
using ::testing::Pair;
using ::testing::UnorderedElementsAre;


TEST( IdentifierUtilsTest, ExtractIdentifiersFromTagsFileWorks ) {
  fs::path root = fs::current_path().root_path();
  fs::path testfile = PathToTestFile( "basic.tags" );
  /* VS2017 returns C:\DIRECT~1\ paths without fs::weakly_canonical() */
#ifdef STD_OLD_GCC_7_UBUNTU_1804
  fs::path testfile_parent = fs::canonical( testfile.parent_path() );
#else
  fs::path testfile_parent = fs::weakly_canonical( testfile.parent_path() );
#endif

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ),
      UnorderedElementsAre(
        Pair( "cpp", UnorderedElementsAre(
                         Pair( ( testfile_parent / "foo" ).string(),
                               ElementsAre( "i1", "foosy" ) ),
                         Pair( ( testfile_parent / "bar" ).string(),
                               ElementsAre( "i1", "fooaaa" ) ) ) ),
        Pair( "fakelang", UnorderedElementsAre(
                              Pair( ( root / "foo" ).string(),
                                    ElementsAre( "zoro" ) ) ) ),
        Pair( "cs", UnorderedElementsAre(
                        Pair( ( root / "m_oo" ).string(),
                              ElementsAre( "#bleh" ) ) ) ),
        Pair( "foobar", UnorderedElementsAre(
                            Pair( ( testfile_parent / "foo.bar" ).string(),
                                  ElementsAre( "API", "DELETE" ) ) ) ),
        Pair( "c", UnorderedElementsAre(
                       Pair( ( root / "foo" / "zoo" ).string(),
                             ElementsAre( "Floo::goo" ) ),
                       Pair( ( root / "foo" / "goo maa" ).string(),
                             ElementsAre( "!goo" ) ) ) ) ) );
}


TEST( IdentifierUtilsTest, TagFileIsDirectory ) {
  fs::path testfile = PathToTestFile( "directory.tags" );

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ), IsEmpty() );
}


TEST( IdentifierUtilsTest, TagFileIsEmpty ) {
  fs::path testfile = PathToTestFile( "empty.tags" );

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ), IsEmpty() );
}


TEST( IdentifierUtilsTest, TagLanguageMissing ) {
  fs::path testfile = PathToTestFile( "invalid_tag_file_format.tags" );

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ), IsEmpty() );
}


TEST( IdentifierUtilsTest, TagFileInvalidPath ) {
  fs::path testfile = PathToTestFile( "invalid_path_to_tag_file.tags" );

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ), IsEmpty() );
}

} // namespace YouCompleteMe

