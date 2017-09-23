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

#ifndef EXCEPTIONS_H_3PHJ9YOB
#define EXCEPTIONS_H_3PHJ9YOB

#include <exception>

namespace YouCompleteMe {

// YouCompleteMe uses the "Exception types as semantic tags" idiom.
// For more information, see this link:
//   http://www.boost.org/doc/libs/1_50_0/libs/exception/doc/exception_types_as_simple_semantic_tags.html

/**
 * Thrown when a file does not exist.
 */
struct YCM_EXPORT ClangParseError : virtual std::exception {};

/**
 * Thrown when an error occurs while decoding a UTF-8 string.
 */
struct YCM_EXPORT UnicodeDecodeError : virtual std::exception {};

} // namespace YouCompleteMe

#endif /* end of include guard: EXCEPTIONS_H_3PHJ9YOB */

