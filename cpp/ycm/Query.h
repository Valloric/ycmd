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

#ifndef QUERY_H_39D9SMCE
#define QUERY_H_39D9SMCE

#include "Word.h"

#include <string>
#include <vector>

namespace YouCompleteMe {

class Query : public Word {
public:
  YCM_EXPORT explicit Query( const std::string &text );
  // Make class noncopyable
  Query( const Query& ) = delete;
  Query& operator=( const Query& ) = delete;
};

} // namespace YouCompleteMe

#endif /* end of include guard: QUERY_H_39D9SMCE */
