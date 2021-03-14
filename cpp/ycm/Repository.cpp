// Copyright (C) 2021 ycmd contributors
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

#define YCM_IS_CPP
#include "Repository.h"

namespace YouCompleteMe {
template class YCM_EXPORT Repository< Candidate >;
template class YCM_EXPORT Repository< Character >;
template class YCM_EXPORT Repository< CodePoint >;
} // namespace YouCompleteMe
