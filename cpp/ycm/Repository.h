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

#ifndef REPOSITORY_H_36TXTS6C
#define REPOSITORY_H_36TXTS6C

#include "Candidate.h"
#include "Character.h"
#include "CodePoint.h"
#include "Utils.h"

#include <memory>
#include <shared_mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace YouCompleteMe {

// This singleton stores already built T objects. If Ts are requested for
// previously unseen strings, new T objects are built.
//
// This class is thread-safe.
template< typename T >
class Repository {
public:
  using Holder = std::unordered_map< std::string, std::unique_ptr< T > >;
  using Sequence = std::vector< const T* >;
  YCM_EXPORT static Repository &Instance() {
    static Repository repo;
    return repo;
  }
  // Make class noncopyable
  Repository( const Repository& ) = delete;
  Repository& operator=( const Repository& ) = delete;

  YCM_EXPORT size_t NumStoredElements() const {
    std::shared_lock locker( element_holder_mutex_ );
    return element_holder_.size();
  }

  YCM_EXPORT Sequence GetElements(
    std::vector< std::string >&& elements ) {
    Sequence element_objects( elements.size() );
    auto it = element_objects.begin();
  
    {
      std::lock_guard locker( element_holder_mutex_ );
  
      for ( auto&& element : elements ) {
        if constexpr ( std::is_same_v< T, Candidate > ) {
          if ( element.size() > 80 ) {
            element = "";
          }
        }
        std::unique_ptr< T > &element_object = GetValueElseInsert(
                                                           element_holder_,
                                                           element,
                                                           nullptr );
  
        if ( !element_object ) {
          element_object = std::make_unique< T >( std::move( element ) );
        }
  
        *it++ = element_object.get();
      }
    }
  
    return element_objects;
  }

  // This should only be used to isolate tests and benchmarks.
  YCM_EXPORT void ClearElements() {
    element_holder_.clear();
  }

private:
  Repository() = default;
  ~Repository() = default;

  // This data structure owns all the T pointers
  Holder element_holder_;
  mutable std::shared_mutex element_holder_mutex_;
};

#ifndef YCM_IS_CPP
extern template class Repository< Candidate >;
extern template class Repository< Character >;
extern template class Repository< CodePoint >;
#endif

} // namespace YouCompleteMe

#endif /* end of include guard: REPOSITORY_H_36TXTS6C */
