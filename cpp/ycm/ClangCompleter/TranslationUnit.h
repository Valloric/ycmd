// Copyright (C) 2011, 2012  Google Inc.
//
// This file is part of YouCompleteMe.
//
// YouCompleteMe is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// YouCompleteMe is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

#ifndef TRANSLATIONUNIT_H_XQ7I6SVA
#define TRANSLATIONUNIT_H_XQ7I6SVA

#include "../DLLDefines.h"
#include "UnsavedFile.h"
#include "Diagnostic.h"
#include "Token.h"
#include "Location.h"
#include "Documentation.h"

#include <clang-c/Index.h>
#include <boost/utility.hpp>
#include <boost/thread/mutex.hpp>

#include <string>
#include <vector>

namespace YouCompleteMe {

struct CompletionData;
typedef boost::shared_ptr< std::vector< CompletionData > > AsyncCompletions;

class TranslationUnit : boost::noncopyable {
public:

  // This constructor creates an invalid, sentinel TU. All of it's methods
  // return empty vectors, and IsCurrentlyUpdating always returns true so that
  // no callers try to rely on the invalid TU.
  TranslationUnit();

  YCM_DLL_EXPORT TranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags,
    CXIndex clang_index );

  YCM_DLL_EXPORT ~TranslationUnit();

  void Destroy();

  std::vector< Diagnostic > LatestDiagnostics();

  bool IsCurrentlyUpdating() const;

  std::vector< Diagnostic > Reparse(
    const std::vector< UnsavedFile > &unsaved_files );

  std::vector< CompletionData > CandidatesForLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files );

  YCM_DLL_EXPORT Location GetDeclarationLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  YCM_DLL_EXPORT Location GetDefinitionLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  std::string GetTypeAtLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  std::string GetEnclosingFunctionAtLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  std::vector< FixIt > GetFixItsForLocationInFile(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  DocumentationData GetDocsForLocationInFile(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    bool reparse = true );

  std::vector< Token > GetSemanticTokens(
    uint start_line,
    uint start_column,
    uint end_line,
    uint end_column );

private:
  void Reparse( std::vector< CXUnsavedFile > &unsaved_files );

  void Reparse( std::vector< CXUnsavedFile > &unsaved_files,
                uint parse_options );

  void UpdateLatestDiagnostics();

  CXFile GetFile();

  CXSourceLocation GetLocation( CXFile file, int line, int column );

  CXSourceLocation GetLocation( int line, int column );

  CXCursor GetCursor( int line, int column );

  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  std::string filename_;

  boost::mutex diagnostics_mutex_;
  std::vector< Diagnostic > latest_diagnostics_;

  mutable boost::mutex clang_access_mutex_;
  CXTranslationUnit clang_translation_unit_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: TRANSLATIONUNIT_H_XQ7I6SVA */

