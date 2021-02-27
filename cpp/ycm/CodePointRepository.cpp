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

#include "CodePointRepository.h"
#include "CodePoint.h"
#include "Utils.h"

namespace YouCompleteMe {

CodePointRepository &CodePointRepository::Instance() {
  static CodePointRepository repo;
  return repo;
}


size_t CodePointRepository::NumStoredCodePoints() const {
  std::shared_lock locker( code_point_holder_mutex_ );
  return code_point_holder_.size();
}


CodePointSequence CodePointRepository::GetCodePoints(
  const std::vector< std::string > &code_points ) {
  CodePointSequence code_point_objects( code_points.size() );
  auto it = code_point_objects.begin();

  {
    std::lock_guard locker( code_point_holder_mutex_ );

    for ( std::string_view code_point : code_points ) {
      std::unique_ptr< CodePoint > &code_point_object = GetValueElseInsert(
                                                          code_point_holder_,
                                                          code_point,
                                                          nullptr );

      if ( !code_point_object ) {
        code_point_object = std::make_unique< CodePoint >( code_point );
      }

      *it++ = code_point_object.get();
    }
  }

  return code_point_objects;
}


void CodePointRepository::ClearCodePoints() {
  code_point_holder_.clear();
}


} // namespace YouCompleteMe
