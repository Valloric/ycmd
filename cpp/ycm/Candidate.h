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

#ifndef CANDIDATE_H_R5LZH6AC
#define CANDIDATE_H_R5LZH6AC

#include "Word.h"

#include <memory>
#include <string>

namespace YouCompleteMe {

class Result;

class Candidate : public Word {
public:

  YCM_EXPORT explicit Candidate( const std::string &text );
  // Make class noncopyable
  Candidate( const Candidate& ) = delete;
  Candidate& operator=( const Candidate& ) = delete;
  ~Candidate() = default;

  inline const std::string &CaseSwappedText() const {
    return case_swapped_text_;
  }

  inline const std::vector< const Character * > &WordBoundaryChars() const {
    return word_boundary_chars_;
  }

  inline bool TextIsLowercase() const {
    return text_is_lowercase_;
  }

  // Check if the query is a subsequence of the candidate and return a result
  // accordingly. This is done by simultaneously going through the characters of
  // the query and the candidate. If both characters match, we move to the next
  // character in the query and the candidate. Otherwise, we only move to the
  // next character in the candidate. The matching is case-insensitive if the
  // character of the query is lowercase. If there is no character left in the
  // query, the query is not a subsequence and we return an empty result. If
  // there is no character left in the candidate, the query is a subsequence and
  // we return a result with the query, the candidate, the sum of indexes of the
  // candidate where characters matched, and a boolean that is true if the query
  // is a prefix of the candidate.
  YCM_EXPORT Result QueryMatchResult( const Word &query ) const;

private:
  void ComputeCaseSwappedText();
  void ComputeTextIsLowercase();
  void ComputeWordBoundaryChars();

  std::string case_swapped_text_;
  std::vector< const Character * > word_boundary_chars_;
  bool text_is_lowercase_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CANDIDATE_H_R5LZH6AC */

