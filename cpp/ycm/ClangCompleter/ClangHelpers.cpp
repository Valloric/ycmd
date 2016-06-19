// Copyright (C) 2013 Google Inc.
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

#include "standard.h"
#include "ClangHelpers.h"
#include "ClangUtils.h"
#include "Utils.h"
#include "UnsavedFile.h"
#include "Location.h"
#include "Range.h"
#include "PythonSupport.h"

#include <boost/unordered_map.hpp>
#include <iostream>

using boost::unordered_map;

namespace YouCompleteMe {
namespace {

DiagnosticKind DiagnosticSeverityToType( CXDiagnosticSeverity severity ) {
  switch ( severity ) {
    case CXDiagnostic_Ignored:
    case CXDiagnostic_Note:
      return INFORMATION;

    case CXDiagnostic_Warning:
      return WARNING;

    case CXDiagnostic_Error:
    case CXDiagnostic_Fatal:
    default:
      return ERROR;
  }
}

FixIt BuildFixIt( const std::string& text,
                  CXDiagnostic diagnostic ) {
  FixIt fixit;

  uint num_chunks = clang_getDiagnosticNumFixIts( diagnostic );
  if ( !num_chunks )
    return fixit;

  fixit.chunks.reserve( num_chunks );
  fixit.location = Location( clang_getDiagnosticLocation( diagnostic ) );
  fixit.text = text;

  for ( uint idx = 0; idx < num_chunks; ++idx ) {
    FixItChunk chunk;
    CXSourceRange sourceRange;
    chunk.replacement_text = CXStringToString(
                               clang_getDiagnosticFixIt( diagnostic,
                                                         idx,
                                                         &sourceRange ) );

    chunk.range = sourceRange;
    fixit.chunks.push_back( chunk );
  }

  return fixit;
}

/// This method generates a FixIt object for the supplied diagnostic, and any
/// child diagnostics (recursively), should a FixIt be available and appends
/// them to fixits.
/// Similarly it populates full_diagnostic_text with a concatenation of the
/// diagnostic text for the supplied diagnostic and each child diagnostic
/// (recursively).
/// Warning: This method is re-entrant (recursive).
void BuildFullDiagnosticDataFromChildren(
  std::string& full_diagnostic_text,
  std::vector< FixIt >& fixits,
  CXDiagnostic diagnostic ) {

  std::string diag_text = CXStringToString( clang_formatDiagnostic(
                              diagnostic,
                              clang_defaultDiagnosticDisplayOptions() ) );

  full_diagnostic_text.append( diag_text );

  // Populate any fixit attached to this diagnostic.
  FixIt fixit = BuildFixIt( diag_text, diagnostic );
  if ( fixit.chunks.size() > 0 )
    fixits.push_back( fixit );

  // Note: clang docs say that a CXDiagnosticSet retrieved with
  // clang_getChildDiagnostics do NOT need to be released with
  // clang_diposeDiagnosticSet
  CXDiagnosticSet diag_set = clang_getChildDiagnostics( diagnostic );

  if ( !diag_set )
    return;

  uint num_child_diagnostics = clang_getNumDiagnosticsInSet( diag_set );

  if ( !num_child_diagnostics )
    return;

  for ( uint i = 0; i < num_child_diagnostics; ++i ) {
    CXDiagnostic child_diag = clang_getDiagnosticInSet( diag_set, i );

    if( !child_diag )
      continue;

    full_diagnostic_text.append( "\n" );

    // recurse
    BuildFullDiagnosticDataFromChildren( full_diagnostic_text,
                                         fixits,
                                         child_diag );
  }
}

// Returns true when the provided completion string is available to the user;
// unavailable completion strings refer to entities that are private/protected,
// deprecated etc.
bool CompletionStringAvailable( CXCompletionString completion_string ) {
  if ( !completion_string )
    return false;

  return clang_getCompletionAvailability( completion_string ) ==
         CXAvailability_Available;
}


std::vector< Range > GetRanges( const DiagnosticWrap &diagnostic_wrap ) {
  std::vector< Range > ranges;
  uint num_ranges = clang_getDiagnosticNumRanges( diagnostic_wrap.get() );
  ranges.reserve( num_ranges );

  for ( uint i = 0; i < num_ranges; ++i ) {
    ranges.push_back(
      Range( clang_getDiagnosticRange( diagnostic_wrap.get(), i ) ) );
  }

  return ranges;
}


Range GetLocationExtent( CXSourceLocation source_location,
                         CXTranslationUnit translation_unit ) {
  // If you think the below code is an idiotic way of getting the source range
  // for an identifier at a specific source location, you are not the only one.
  // I cannot believe that this is the only way to achieve this with the
  // libclang API in a robust way.
  // I've tried many simpler ways of doing this and they all fail in various
  // situations.

  CXSourceRange range = clang_getCursorExtent(
                          clang_getCursor( translation_unit, source_location ) );
  CXToken *tokens;
  uint num_tokens;
  clang_tokenize( translation_unit, range, &tokens, &num_tokens );

  Location location( source_location );
  Range final_range;

  for ( uint i = 0; i < num_tokens; ++i ) {
    Location token_location( clang_getTokenLocation( translation_unit,
                                                     tokens[ i ] ) );

    if ( token_location == location ) {
      std::string name = CXStringToString(
                           clang_getTokenSpelling( translation_unit, tokens[ i ] ) );
      Location end_location = location;
      end_location.column_number_ += name.length();
      final_range = Range( location, end_location );
      break;
    }
  }

  clang_disposeTokens( translation_unit, tokens, num_tokens );
  return final_range;
}


} // unnamed namespace

std::vector< CXUnsavedFile > ToCXUnsavedFiles(
  const std::vector< UnsavedFile > &unsaved_files ) {
  std::vector< CXUnsavedFile > clang_unsaved_files( unsaved_files.size() );

  for ( uint i = 0; i < unsaved_files.size(); ++i ) {
    clang_unsaved_files[ i ].Filename = unsaved_files[ i ].filename_.c_str();
    clang_unsaved_files[ i ].Contents = unsaved_files[ i ].contents_.c_str();
    clang_unsaved_files[ i ].Length   = unsaved_files[ i ].length_;
  }

  return clang_unsaved_files;
}


std::vector< CompletionData > ToCompletionDataVector(
  CXCodeCompleteResults *results ) {
  std::vector< CompletionData > completions;

  if ( !results || !results->Results )
    return completions;

  completions.reserve( results->NumResults );
  unordered_map< std::string, uint > seen_data;

  for ( uint i = 0; i < results->NumResults; ++i ) {
    CXCompletionResult completion_result = results->Results[ i ];

    if ( !CompletionStringAvailable( completion_result.CompletionString ) )
      continue;

    CompletionData data( completion_result );
    uint index = GetValueElseInsert( seen_data,
                                     data.original_string_,
                                     completions.size() );

    if ( index == completions.size() ) {
      completions.push_back( boost::move( data ) );
    }

    else {
      // If we have already seen this completion, then this is an overload of a
      // function we have seen. We add the signature of the overload to the
      // detailed information.
      completions[ index ].detailed_info_
      .append( data.return_type_ )
      .append( " " )
      .append( data.everything_except_return_type_ )
      .append( "\n" );
    }
  }

  return completions;
}


Diagnostic BuildDiagnostic( DiagnosticWrap diagnostic_wrap,
                            CXTranslationUnit translation_unit ) {
  Diagnostic diagnostic;

  if ( !diagnostic_wrap )
    return diagnostic;

  diagnostic.kind_ = DiagnosticSeverityToType(
                       clang_getDiagnosticSeverity( diagnostic_wrap.get() ) );

  // If this is an "ignored" diagnostic, there's no point in continuing since we
  // won't display those to the user
  if ( diagnostic.kind_ == INFORMATION )
    return diagnostic;

  CXSourceLocation source_location =
    clang_getDiagnosticLocation( diagnostic_wrap.get() );
  diagnostic.location_ = Location( source_location );
  diagnostic.location_extent_ = GetLocationExtent( source_location,
                                                   translation_unit );
  diagnostic.ranges_ = GetRanges( diagnostic_wrap );
  diagnostic.text_ = CXStringToString(
                       clang_getDiagnosticSpelling( diagnostic_wrap.get() ) );

  BuildFullDiagnosticDataFromChildren( diagnostic.long_formatted_text_,
                                       diagnostic.fixits_,
                                       diagnostic_wrap.get() );

  return diagnostic;
}

} // namespace YouCompleteMe
