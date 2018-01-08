// Copyright (C) 2011-2018 ycmd contributors
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
#include "Candidate.h"
#include "Result.h"

#include <iostream>

using ::testing::ContainerEq;

namespace YouCompleteMe {

void WordBoundaryCharsTest( const std::string &candidate,
                            const std::string &boundary_chars ) {
  EXPECT_THAT( Candidate( candidate ).WordBoundaryChars(),
               ContainerEq( Word( boundary_chars ).Characters() ) );
}

TEST( WordBoundaryCharsTest, SimpleOneWord ) {
  WordBoundaryCharsTest( "simple", "s" );
}

TEST( WordBoundaryCharsTest, PunctuationInMiddle ) {
  WordBoundaryCharsTest( "simple_foo", "sf" );
}

TEST( WordBoundaryCharsTest, PunctuationStart ) {
  WordBoundaryCharsTest( "_simple", "s" );
  WordBoundaryCharsTest( ".simple", "s" );
  WordBoundaryCharsTest( "/simple", "s" );
  WordBoundaryCharsTest( ":simple", "s" );
  WordBoundaryCharsTest( "-simple", "s" );
  WordBoundaryCharsTest( "«simple", "s" );
  WordBoundaryCharsTest( "…simple", "s" );
  WordBoundaryCharsTest( "𐬺simple", "s" );
}

TEST( WordBoundaryCharsTest, PunctuationStartButFirstDigit ) {
  WordBoundaryCharsTest( "_1simple", "" );
  WordBoundaryCharsTest( "_1simPle", "P" );
  WordBoundaryCharsTest( "…𝟝simple", "" );
  WordBoundaryCharsTest( "…𝟝simPle", "P" );
}

TEST( WordBoundaryCharsTest, ManyPunctuationStart ) {
  WordBoundaryCharsTest( "___simple", "s" );
  WordBoundaryCharsTest( ".;/simple", "s" );
  WordBoundaryCharsTest( "«…𐬺simple", "s" );
}

TEST( WordBoundaryCharsTest, PunctuationStartAndInMiddle ) {
  WordBoundaryCharsTest( "_simple_foo", "sf" );
  WordBoundaryCharsTest( "/simple.foo", "sf" );
  WordBoundaryCharsTest( "𐬺simple—foo", "sf" );
}

TEST( WordBoundaryCharsTest, ManyPunctuationStartAndInMiddle ) {
  WordBoundaryCharsTest( "___simple__foo", "sf" );
  WordBoundaryCharsTest( "./;:simple..foo", "sf" );
  WordBoundaryCharsTest( "«𐬺…simple——foo", "sf" );
}

TEST( WordBoundaryCharsTest, SimpleCapitalStart ) {
  WordBoundaryCharsTest( "Simple", "S" );
  WordBoundaryCharsTest( "Σimple", "Σ" );
}

TEST( WordBoundaryCharsTest, SimpleCapitalTwoWord ) {
  WordBoundaryCharsTest( "SimpleStuff", "SS" );
  WordBoundaryCharsTest( "ΣimpleΣtuff", "ΣΣ" );
}

TEST( WordBoundaryCharsTest, SimpleCapitalTwoWordPunctuationMiddle ) {
  WordBoundaryCharsTest( "Simple_Stuff", "SS" );
  WordBoundaryCharsTest( "Σimple…Σtuff", "ΣΣ" );
}

TEST( WordBoundaryCharsTest, JavaCase ) {
  WordBoundaryCharsTest( "simpleStuffFoo", "sSF" );
  WordBoundaryCharsTest( "σimpleΣtuffΦoo", "σΣΦ" );
}

TEST( WordBoundaryCharsTest, UppercaseSequence ) {
  WordBoundaryCharsTest( "simpleSTUFF", "sS" );
  WordBoundaryCharsTest( "σimpleΣTUFF", "σΣ" );
}

TEST( WordBoundaryCharsTest, UppercaseSequenceInMiddle ) {
  WordBoundaryCharsTest( "simpleSTUFFfoo", "sS" );
  WordBoundaryCharsTest( "σimpleΣTUFFφoo", "σΣ" );
}

TEST( WordBoundaryCharsTest, UppercaseSequenceInMiddlePunctuation ) {
  WordBoundaryCharsTest( "simpleSTUFF_Foo", "sSF" );
  WordBoundaryCharsTest( "σimpleΣTUFF…Φoo", "σΣΦ" );
}

TEST( WordBoundaryCharsTest, UppercaseSequenceInMiddlePunctuationLowercase ) {
  WordBoundaryCharsTest( "simpleSTUFF_foo", "sSf" );
  WordBoundaryCharsTest( "simpleSTUFF.foo", "sSf" );
  WordBoundaryCharsTest( "σimpleΣTUFF…φoo", "σΣφ" );
}

TEST( WordBoundaryCharsTest, AllCapsSimple ) {
  WordBoundaryCharsTest( "SIMPLE", "S" );
  WordBoundaryCharsTest( "ΣIMPLE", "Σ" );
}

TEST( GetWordBoundaryCharsTest, AllCapsPunctuationStart ) {
  WordBoundaryCharsTest( "_SIMPLE", "S" );
  WordBoundaryCharsTest( ".SIMPLE", "S" );
  WordBoundaryCharsTest( "«ΣIMPLE", "Σ" );
  WordBoundaryCharsTest( "…ΣIMPLE", "Σ" );
}

TEST( WordBoundaryCharsTest, AllCapsPunctuationMiddle ) {
  WordBoundaryCharsTest( "SIMPLE_STUFF", "SS" );
  WordBoundaryCharsTest( "SIMPLE/STUFF", "SS" );
  WordBoundaryCharsTest( "SIMPLE—ΣTUFF", "SΣ" );
  WordBoundaryCharsTest( "ΣIMPLE…STUFF", "ΣS" );
}

TEST( WordBoundaryCharsTest, AllCapsPunctuationMiddleAndStart ) {
  WordBoundaryCharsTest( "_SIMPLE_STUFF", "SS" );
  WordBoundaryCharsTest( ":SIMPLE.STUFF", "SS" );
  WordBoundaryCharsTest( "«ΣIMPLE—ΣTUFF", "ΣΣ" );
  WordBoundaryCharsTest( "𐬺SIMPLE—ΣTUFF", "SΣ" );
}

TEST( CandidateTest, TextValid ) {
  std::string text = "foo";
  Candidate candidate( text );

  EXPECT_EQ( text, candidate.Text() );
}

TEST( CandidateTest, QueryMatchResultCaseSensitiveIsSubsequence ) {
  std::string candidate = "F𐍈oβaＡAr";
  std::vector< std::string > queries = {
    "F𐍈oβaＡAr",
    "FβＡA",
    "F",
    "ＡA",
    "A",
    "β",
    "f𐍈oβaａar",
    "f𐍈oβaＡAr",
    "fβＡA",
    "fβaa",
    "β",
    "f",
    "fβａr"
  };

  for ( const std::string &query : queries ) {
    Result result = Candidate( candidate ).QueryMatchResult( Word( query ) );
    EXPECT_TRUE( result.IsSubsequence() )
      << query << " is expected to be a subsequence of " << candidate;
  }
}

TEST( CandidateTest, QueryMatchResultCaseSensitiveIsntSubsequence ) {
  std::string candidate = "F𐍈oβaＡAr";
  std::vector< std::string > queries = {
    "g𐍈o",
    "R",
    "O",
    "𐍈O",
    "OβA",
    "FβAR",
    "FβＡAR",
    "Oar",
    "F𐍈oβaＡＡr",
    "F𐍈OβaＡAr",
    "F𐍈Oβaａar",
    "f𐍈Oβaａar",
    "f𐍈oβaａaR"
  };

  for ( const std::string &query : queries ) {
    Result result = Candidate( candidate ).QueryMatchResult( Word( query ) );
    EXPECT_FALSE( result.IsSubsequence() )
      << query << " is not expected to be a subsequence of " << candidate;
  }
}

} // namespace YouCompleteMe
