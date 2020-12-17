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

#include "PythonSupport.h"
#include "Candidate.h"
#include "CandidateRepository.h"
#include "Result.h"
#include "Utils.h"

#include <utility>
#include <vector>

using pybind11::len;
using pybind11::str;
using pybind11::bytes;
using pybind11::object;
using pybind11::isinstance;
using pylist = pybind11::list;

namespace YouCompleteMe {

namespace {

std::vector< const Candidate * > CandidatesFromObjectList(
  const pybind11::list& candidates,
  pybind11::str candidate_property,
  size_t num_candidates ) {
  std::vector< std::string > candidate_strings;
  candidate_strings.reserve( num_candidates );

  if ( !PyUnicode_GET_LENGTH( candidate_property.ptr() ) ) {
    for ( size_t i = 0; i < num_candidates; ++i ) {
        candidate_strings.emplace_back( GetUtf8String( PyList_GET_ITEM(candidates.ptr(), i ) ) );
    }
  } else {
    for ( size_t i = 0; i < num_candidates; ++i ) {
        auto element = PyDict_GetItem( PyList_GET_ITEM( candidates.ptr(), i ),
                                        candidate_property.ptr() );
        candidate_strings.emplace_back( GetUtf8String( element ) );
    }
  }

  return CandidateRepository::Instance().GetCandidatesForStrings(
           std::move( candidate_strings ) );
}

} // unnamed namespace


pylist FilterAndSortCandidates(
  const pylist& candidates,
  pybind11::str candidate_property,
  std::string query,
  const size_t max_candidates ) {
  pylist filtered_candidates;

  size_t num_candidates = len( candidates );
  std::vector< const Candidate * > repository_candidates =
    CandidatesFromObjectList( candidates, std::move( candidate_property ), num_candidates );

  std::vector< ResultAnd< size_t > > result_and_objects;
  {
    pybind11::gil_scoped_release unlock;
    Word query_object( std::move( query ) );

    for ( size_t i = 0; i < num_candidates; ++i ) {
      const Candidate *candidate = repository_candidates[ i ];

      if ( candidate->IsEmpty() || !candidate->ContainsBytes( query_object ) ) {
        continue;
      }

      Result result = candidate->QueryMatchResult( query_object );

      if ( result.IsSubsequence() ) {
        result_and_objects.emplace_back( result, i );
      }
    }

    PartialSort( result_and_objects, max_candidates );
  }

  for ( const ResultAnd< size_t > &result_and_object : result_and_objects ) {
    auto new_candidate = 
        PyList_GET_ITEM( candidates.ptr(), result_and_object.extra_object_ );
    filtered_candidates.append( new_candidate );
  }

  return filtered_candidates;
}


std::string GetUtf8String( pybind11::handle value ) {
  // If already a unicode or string (or something derived from it)
  // pybind will already convert to utf8 when converting to std::string.
  // For `bytes` the contents are left untouched:
  if ( PyUnicode_CheckExact( value.ptr() ) ) {
    ssize_t size = 0;
    const char* buffer = nullptr;
    buffer = PyUnicode_AsUTF8AndSize( value.ptr(), &size );
    return { buffer, (size_t)size };
  }
  if ( PyBytes_CheckExact( value.ptr() ) ) {
    ssize_t size = 0;
    char* buffer = nullptr;
    PyBytes_AsStringAndSize( value.ptr(), &buffer, &size );
    return { buffer, (size_t)size };
  }

  // Otherwise go through Python's built-in `str`.
  ssize_t size = 0;
  const char* buffer =
      PyUnicode_AsUTF8AndSize( PyObject_Str( value.ptr() ), &size );
  return { buffer, (size_t)size };
}

} // namespace YouCompleteMe
