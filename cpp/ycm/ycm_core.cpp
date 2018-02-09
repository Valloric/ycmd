// Copyright (C) 2011, 2012 Google Inc.
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

/*
 * iostream is included because there's a bug with python
 * earlier than 2.7.12 and 3.5.3 on OSX and FreeBSD.
 * When either no one else is using earlier versions of python
 * or ycmd drops support for those, this include statement can be removed.
 * Needs to be the absolute first header, so that it is imported
 * before anything python related.
 */
#include <iostream>
#include "IdentifierCompleter.h"
#include "PythonSupport.h"
#include "versioning.h"
#include <pybind11/stl_bind.h>

#ifdef USE_CLANG_COMPLETER
#  include "ClangCompleter.h"
#  include "ClangUtils.h"
#  include "CompletionData.h"
#  include "Diagnostic.h"
#  include "Location.h"
#  include "Range.h"
#  include "UnsavedFile.h"
#  include "CompilationDatabase.h"
#  include "Documentation.h"
#endif // USE_CLANG_COMPLETER

using namespace pybind11;
using namespace YouCompleteMe;

bool HasClangSupport() {
#ifdef USE_CLANG_COMPLETER
  return true;
#else
  return false;
#endif // USE_CLANG_COMPLETER
}

PYBIND11_MAKE_OPAQUE( std::vector< std::string > );
#ifdef USE_CLANG_COMPLETER
PYBIND11_MAKE_OPAQUE( std::vector< UnsavedFile > );
PYBIND11_MAKE_OPAQUE( std::vector< YouCompleteMe::Range > );
PYBIND11_MAKE_OPAQUE( std::vector< YouCompleteMe::CompletionData > );
PYBIND11_MAKE_OPAQUE( std::vector< YouCompleteMe::Diagnostic > );
PYBIND11_MAKE_OPAQUE( std::vector< YouCompleteMe::FixIt > );
PYBIND11_MAKE_OPAQUE( std::vector< YouCompleteMe::FixItChunk > );
#endif // USE_CLANG_COMPLETER

PYBIND11_MODULE(ycm_core, m)
{
  // Necessary because of usage of the ReleaseGil class
  PyEval_InitThreads();

  m.def( "HasClangSupport", &HasClangSupport );

  m.def( "FilterAndSortCandidates",
         &FilterAndSortCandidates,
	 arg("candidates"),
	 arg("candidate_property"),
	 arg("query"),
	 arg("max_candidates") = 0 );

  m.def( "YcmCoreVersion", &YcmCoreVersion );

  // This is exposed so that we can test it.
#if PY_MAJOR_VERSION >= 3
  m.def( "GetUtf8String", &GetUtf8String );
#else
  m.def( "GetUtf8String",
	 []( const object &value ) {
	   return bytes( GetUtf8String( value ) );
	 } );
#endif

  class_< IdentifierCompleter >( m, "IdentifierCompleter" )
    .def( init<>() )
    .def( "AddIdentifiersToDatabase",
          &IdentifierCompleter::AddIdentifiersToDatabase )
    .def( "ClearForFileAndAddIdentifiersToDatabase",
          &IdentifierCompleter::ClearForFileAndAddIdentifiersToDatabase )
    .def( "AddIdentifiersToDatabaseFromTagFiles",
          &IdentifierCompleter::AddIdentifiersToDatabaseFromTagFiles )
    .def( "CandidatesForQueryAndType",
          &IdentifierCompleter::CandidatesForQueryAndType,
	  arg( "query" ),
	  arg( "filetype" ),
	  arg( "max_candidates" ) = 0 );

  bind_vector< std::vector< std::string > >( m, "StringVector" );

#ifdef USE_CLANG_COMPLETER
  register_exception< ClangParseError >(m, "ClangParseError" );

  m.def( "ClangVersion", ClangVersion );

  // CAREFUL HERE! For filename and contents we are referring directly to
  // Python-allocated and -managed memory since we are accepting pointers to
  // data members of python objects. We need to ensure that those objects
  // outlive our UnsavedFile objects.
  class_< UnsavedFile >( m, "UnsavedFile" )
    .def( init<>() )
    .def_readwrite( "filename_", &UnsavedFile::filename_ )
    .def_readwrite( "contents_", &UnsavedFile::contents_ )
    .def_readwrite( "length_", &UnsavedFile::length_ );

  bind_vector< std::vector< UnsavedFile > >( m, "UnsavedFileVector" );

  class_< ClangCompleter >( m, "ClangCompleter" )
    .def( init<>() )
    .def( "GetDeclarationLocation", &ClangCompleter::GetDeclarationLocation )
    .def( "GetDefinitionLocation", &ClangCompleter::GetDefinitionLocation )
    .def( "DeleteCachesForFile", &ClangCompleter::DeleteCachesForFile )
    .def( "UpdatingTranslationUnit", &ClangCompleter::UpdatingTranslationUnit )
    .def( "UpdateTranslationUnit", &ClangCompleter::UpdateTranslationUnit )
    .def( "CandidatesForLocationInFile",
          &ClangCompleter::CandidatesForLocationInFile )
    .def( "GetTypeAtLocation", &ClangCompleter::GetTypeAtLocation )
    .def( "GetEnclosingFunctionAtLocation",
          &ClangCompleter::GetEnclosingFunctionAtLocation )
    .def( "GetFixItsForLocationInFile",
          &ClangCompleter::GetFixItsForLocationInFile )
    .def( "GetDocsForLocationInFile",
          &ClangCompleter::GetDocsForLocationInFile );

  enum_< CompletionKind >( m, "CompletionKind" )
    .value( "STRUCT", STRUCT )
    .value( "CLASS", CLASS )
    .value( "ENUM", ENUM )
    .value( "TYPE", TYPE )
    .value( "MEMBER", MEMBER )
    .value( "FUNCTION", FUNCTION )
    .value( "VARIABLE", VARIABLE )
    .value( "MACRO", MACRO )
    .value( "PARAMETER", PARAMETER )
    .value( "NAMESPACE", NAMESPACE )
    .value( "UNKNOWN", UNKNOWN )
    .export_values();

  class_< CompletionData >( m, "CompletionData" )
    .def( init<>() )
    .def( "TextToInsertInBuffer", &CompletionData::TextToInsertInBuffer )
    .def( "MainCompletionText", &CompletionData::MainCompletionText )
    .def( "ExtraMenuInfo", &CompletionData::ExtraMenuInfo )
    .def( "DetailedInfoForPreviewWindow",
          &CompletionData::DetailedInfoForPreviewWindow )
    .def( "DocString", &CompletionData::DocString )
    .def_readonly( "kind_", &CompletionData::kind_ );

  bind_vector< std::vector< CompletionData > >( m, "CompletionVector" );

  class_< Location >( m, "Location" )
    .def( init<>() )
    .def_readonly( "line_number_", &Location::line_number_ )
    .def_readonly( "column_number_", &Location::column_number_ )
    .def_readonly( "filename_", &Location::filename_ )
    .def( "IsValid", &Location::IsValid );

  class_< Range >( m, "Range" )
    .def( init<>() )
    .def_readonly( "start_", &Range::start_ )
    .def_readonly( "end_", &Range::end_ );

  bind_vector< std::vector< Range > >( m, "RangeVector" );

  class_< FixItChunk >( m, "FixItChunk" )
    .def( init<>() )
    .def_readonly( "replacement_text", &FixItChunk::replacement_text )
    .def_readonly( "range", &FixItChunk::range );

  bind_vector< std::vector< FixItChunk > >( m, "FixItChunkVector" );

  class_< FixIt >( m, "FixIt" )
    .def( init<>() )
    .def_readonly( "chunks", &FixIt::chunks )
    .def_readonly( "location", &FixIt::location )
    .def_readonly( "text", &FixIt::text );

  bind_vector< std::vector< FixIt > >( m, "FixItVector" );

<<<<<<< HEAD
  enum_< DiagnosticKind >( "DiagnosticKind" )
    .value( "ERROR", DiagnosticKind::ERROR )
    .value( "WARNING", DiagnosticKind::WARNING )
    .value( "INFORMATION", DiagnosticKind::INFORMATION );
=======
  enum_< DiagnosticKind >( m, "DiagnosticKind" )
    .value( "ERROR", ERROR )
    .value( "WARNING", WARNING )
    .value( "INFORMATION", INFORMATION )
    .export_values();
>>>>>>> Get back to where you have left - minus the hacks

  class_< Diagnostic >( m, "Diagnostic" )
    .def( init<>() )
    .def_readonly( "ranges_", &Diagnostic::ranges_ )
    .def_readonly( "location_", &Diagnostic::location_ )
    .def_readonly( "location_extent_", &Diagnostic::location_extent_ )
    .def_readonly( "kind_", &Diagnostic::kind_ )
    .def_readonly( "text_", &Diagnostic::text_ )
    .def_readonly( "long_formatted_text_", &Diagnostic::long_formatted_text_ )
    .def_readonly( "fixits_", &Diagnostic::fixits_ );

  bind_vector< std::vector< Diagnostic > >( m, "DiagnosticVector" );

  class_< DocumentationData >( m, "DocumentationData" )
    .def( init<>() )
    .def_readonly( "comment_xml", &DocumentationData::comment_xml )
    .def_readonly( "raw_comment", &DocumentationData::raw_comment )
    .def_readonly( "brief_comment", &DocumentationData::brief_comment )
    .def_readonly( "canonical_type", &DocumentationData::canonical_type )
    .def_readonly( "display_name", &DocumentationData::display_name );

  class_< CompilationDatabase >(
      m, "CompilationDatabase" )
    .def( init< const pybind11::object & >() )
    .def( "DatabaseSuccessfullyLoaded",
          &CompilationDatabase::DatabaseSuccessfullyLoaded )
    .def( "AlreadyGettingFlags",
          &CompilationDatabase::AlreadyGettingFlags )
    .def( "GetCompilationInfoForFile",
          &CompilationDatabase::GetCompilationInfoForFile )
    .def_property_readonly( "database_directory",
                            &CompilationDatabase::GetDatabaseDirectory );

  class_< CompilationInfoForFile,
      std::shared_ptr< CompilationInfoForFile > >(
          m, "CompilationInfoForFile" )
    .def_readonly( "compiler_working_dir_",
                   &CompilationInfoForFile::compiler_working_dir_ )
    .def_readonly( "compiler_flags_",
                   &CompilationInfoForFile::compiler_flags_ );

#endif // USE_CLANG_COMPLETER
}
