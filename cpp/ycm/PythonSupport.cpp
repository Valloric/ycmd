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
#include "Result.h"
#include "Candidate.h"
#include "CandidateRepository.h"
#include "ReleaseGil.h"
#include "Utils.h"

#include <vector>
#include <utility>

using pybind11::len;
using pybind11::str;
using pybind11::object;
using pylist = pybind11::list;

namespace YouCompleteMe {

namespace {

std::vector< const Candidate * > CandidatesFromObjectList(
  const pylist &candidates,
  const std::string &candidate_property ) {
  size_t num_candidates = len( candidates );
  std::vector< std::string > candidate_strings;
  candidate_strings.reserve( num_candidates );

  for ( size_t i = 0; i < num_candidates; ++i ) {
    if ( candidate_property.empty() ) {
      candidate_strings.push_back( GetUtf8String( candidates[ i ] ) );
    } else {
      object holder = candidates[ i ].cast< object >();
      candidate_strings.push_back( GetUtf8String(
                                     holder[ candidate_property.c_str() ] ) );
    }
  }

  return CandidateRepository::Instance().GetCandidatesForStrings(
           candidate_strings );
}

} // unnamed namespace


pylist FilterAndSortCandidates(
  const pylist &candidates,
  const std::string &candidate_property,
  const std::string &query,
  const size_t max_candidates ) {
  pylist filtered_candidates;

  size_t num_candidates = len( candidates );
  std::vector< const Candidate * > repository_candidates =
    CandidatesFromObjectList( candidates, candidate_property );

  std::vector< ResultAnd< size_t > > result_and_objects;
  {
    ReleaseGil unlock;
    Word query_object( query );

    for ( size_t i = 0; i < num_candidates; ++i ) {
      const Candidate *candidate = repository_candidates[ i ];

      if ( candidate->IsEmpty() || !candidate->ContainsBytes( query_object ) ) {
        continue;
      }

      Result result = candidate->QueryMatchResult( query_object );

      if ( result.IsSubsequence() ) {
        ResultAnd< size_t > result_and_object( result, i );
        result_and_objects.push_back( std::move( result_and_object ) );
      }
    }

    PartialSort( result_and_objects, max_candidates );
  }

  for ( const ResultAnd< size_t > &result_and_object : result_and_objects ) {
    filtered_candidates.append( candidates[ result_and_object.extra_object_ ] );
  }

  return filtered_candidates;
}


std::string GetUtf8String( const object &value ) {
  std::string type = value.attr( "__class__" )
                          .attr( "__name__" )
                          .cast< std::string >();

#if PY_MAJOR_VERSION >= 3
  // While strings are internally represented in UCS-2 or UCS-4 on Python 3,
  // they are UTF-8 encoded when converted to std::string.
  if ( type == "str" || type == "bytes" ) {
    return value.cast< std::string >();
  }
#else
  if ( type == "str" ) {
    return value.cast< std::string >();
  }

  if ( type == "unicode" ) {
    // unicode -> str
    return value.attr( "encode" )( "utf8" ).cast< std::string >();
  }

  // newstr and newbytes have a __native__ method that convert them
  // respectively to unicode and str.
  if ( type == "newstr" ) {
    // newstr -> unicode -> str
    return value.attr( "__native__" )()
                .attr( "encode" )( "utf8" )
                .cast< std::string >();
  }

  if ( type == "newbytes" ) {
    // newbytes -> str
    return value.attr( "__native__" )().cast< std::string >();
  }
#endif

  return str( value ).attr( "encode" )( "utf8" ) .cast< std::string >();
}

} // namespace YouCompleteMe
