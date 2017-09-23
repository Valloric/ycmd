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

#include "Query.h"
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

  inline const std::string &CaseSwappedText() const {
    return case_swapped_text_;
  }

  inline const std::vector< const Character * > &WordBoundaryChars() const {
    return word_boundary_chars_;
  }

  inline bool TextIsLowercase() const {
    return text_is_lowercase_;
  }

  YCM_EXPORT Result QueryMatchResult( const Query &query ) const;

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

