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

#include "Candidate.h"
#include "Result.h"

namespace YouCompleteMe {

void Candidate::ComputeCaseSwappedText() {
  for ( const Character *character : Characters() ) {
    if ( character->IsUppercase() ) {
      for ( unsigned char byte : character->Lowercase() )
        case_swapped_text_.push_back( byte );
    } else {
      for ( unsigned char byte : character->Uppercase() )
        case_swapped_text_.push_back( byte );
    }
  }
}


void Candidate::ComputeWordBoundaryChars() {
  const std::vector< const Character * > &characters = Characters();

  auto character = characters.begin();
  if ( character == characters.end() )
    return;

  if ( !( *character )->IsPunctuation() )
    word_boundary_chars_.push_back( *character );

  auto previous_character = characters.begin();
  ++character;
  for ( ; character != characters.end(); ++previous_character, ++character ) {
    if ( ( !( *previous_character )->IsUppercase() &&
           ( *character )->IsUppercase() ) ||
         ( ( *previous_character )->IsPunctuation() &&
           ( *character )->IsLetter() ) )
      word_boundary_chars_.push_back( *character );
  }
}


void Candidate::ComputeTextIsLowercase() {
  for ( const Character *character : Characters() ) {
    if ( character->IsUppercase() ) {
      text_is_lowercase_ = false;
      return;
    }
  }

  text_is_lowercase_ = true;
}


Candidate::Candidate( const std::string &text )
  :
  Word( text ) {
  ComputeCaseSwappedText();
  ComputeWordBoundaryChars();
  ComputeTextIsLowercase();
}


Result Candidate::QueryMatchResult( const Word &query ) const {
  if ( query.IsEmpty() )
    return Result( this, &query, 0, false );

  unsigned query_index = 0;
  unsigned candidate_index = 0;
  unsigned index_sum = 0;

  const std::vector< const Character * > &query_characters = query.Characters();
  const std::vector< const Character * > &candidate_characters = Characters();

  auto query_character_pos = query_characters.begin();
  auto candidate_character_pos = candidate_characters.begin();

  for ( ; candidate_character_pos != candidate_characters.end();
          ++candidate_character_pos, ++candidate_index ) {

    auto candidate_character = *candidate_character_pos;
    auto query_character = *query_character_pos;

    if ( ( !query_character->IsUppercase() &&
           query_character->CaseInsensitivilyEquals( *candidate_character ) ) ||
         *query_character == *candidate_character ) {
      index_sum += candidate_index;

      if ( ++query_character_pos == query_characters.end() )
        return Result( this,
                       &query,
                       index_sum,
                       candidate_index == query_index );

      ++query_index;
    }
  }

  return Result();
}

} // namespace YouCompleteMe
