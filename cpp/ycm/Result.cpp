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

#include "Result.h"
#include "Utils.h"

namespace YouCompleteMe {

namespace {

unsigned LongestCommonSubsequenceLength(
  const std::vector< const Character * > &first,
  const std::vector< const Character * > &second ) {

  const std::vector< const Character * > &longer =
    first.size() > second.size() ? first  : second;
  const std::vector< const Character * > &shorter =
    first.size() > second.size() ? second : first;

  size_t longer_len  = longer.size();
  size_t shorter_len = shorter.size();

  std::vector< unsigned > previous( shorter_len + 1, 0 );
  std::vector< unsigned > current(  shorter_len + 1, 0 );

  for ( size_t i = 0; i < longer_len; ++i ) {
    for ( size_t j = 0; j < shorter_len; ++j ) {
      if ( longer[ i ]->CaseInsensitivilyEquals( *( shorter[ j ] ) ) )
        current[ j + 1 ] = previous[ j ] + 1;
      else
        current[ j + 1 ] = std::max( current[ j ], previous[ j + 1 ] );
    }

    for ( size_t j = 0; j < shorter_len; ++j ) {
      previous[ j + 1 ] = current[ j + 1 ];
    }
  }

  return current[ shorter_len ];
}


} // unnamed namespace

Result::Result()
  :
  is_subsequence_( false ),
  first_char_same_in_query_and_text_( false ),
  ratio_of_word_boundary_chars_in_query_( 0 ),
  word_boundary_char_utilization_( 0 ),
  query_is_candidate_prefix_( false ),
  char_match_index_sum_( 0 ),
  candidate_( NULL ),
  query_( NULL ) {
}


Result::Result( const Candidate *candidate,
                const Query *query,
                unsigned char_match_index_sum,
                bool query_is_candidate_prefix )
  :
  is_subsequence_( true ),
  first_char_same_in_query_and_text_( false ),
  ratio_of_word_boundary_chars_in_query_( 0 ),
  word_boundary_char_utilization_( 0 ),
  query_is_candidate_prefix_( query_is_candidate_prefix ),
  char_match_index_sum_( char_match_index_sum ),
  candidate_( candidate ),
  query_( query ) {
  SetResultFeaturesFromQuery();
}


bool Result::operator< ( const Result &other ) const {
  // Yes, this is ugly but it also needs to be fast.  Since this is called a
  // bazillion times, we have to make sure only the required comparisons are
  // made, and no more.

  if ( *query_ ) {
    if ( first_char_same_in_query_and_text_ !=
         other.first_char_same_in_query_and_text_ )
      return first_char_same_in_query_and_text_;

    bool equal_wb_ratios = num_wb_matches_ == other.num_wb_matches_;

    unsigned ratio =
      num_wb_matches_ * other.candidate_->WordBoundaryChars().size();
    unsigned other_ratio =
      other.num_wb_matches_ * candidate_->WordBoundaryChars().size();

    bool equal_wb_utilization = ratio == other_ratio;

    if ( num_wb_matches_ == query_->Characters().size() ||
         other.num_wb_matches_ == query_->Characters().size() ) {
      if ( !equal_wb_ratios )
        return num_wb_matches_ > other.num_wb_matches_;
      else if ( !equal_wb_utilization )
        return ratio > other_ratio;
    }

    if ( query_is_candidate_prefix_ != other.query_is_candidate_prefix_ )
      return query_is_candidate_prefix_;

    if ( !equal_wb_ratios )
      return num_wb_matches_ > other.num_wb_matches_;
    else if ( !equal_wb_utilization )
      return ratio > other_ratio;

    if ( char_match_index_sum_ != other.char_match_index_sum_ )
      return char_match_index_sum_ < other.char_match_index_sum_;

    if ( Characters().size() != other.Characters().size() )
      return Characters().size() < other.Characters().size();

    if ( candidate_->TextIsLowercase() != other.candidate_->TextIsLowercase() )
      return candidate_->TextIsLowercase();
  }

  // Lexicographic comparison, but we prioritize lowercase letters over
  // uppercase ones. So "foo" < "Foo".
  return candidate_->CaseSwappedText() < other.candidate_->CaseSwappedText();
}


void Result::SetResultFeaturesFromQuery() {
  if ( !*query_ || !*candidate_ )
    return;

  first_char_same_in_query_and_text_ =
    Characters()[ 0 ]->CaseInsensitivilyEquals(
      *( query_->Characters()[ 0 ] ) );

  num_wb_matches_ = LongestCommonSubsequenceLength(
    query_->Characters(), candidate_->WordBoundaryChars() );
}

} // namespace YouCompleteMe
