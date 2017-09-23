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

#ifndef CHARACTER_REPOSITORY_H_36TXTS6C
#define CHARACTER_REPOSITORY_H_36TXTS6C

#include <vector>
#include <string>
#include <unordered_map>
#include <mutex>

namespace YouCompleteMe {

class Character;

typedef std::unordered_map< std::string, const Character * > CharacterHolder;


// This singleton stores already built Character objects for character strings
// that were already seen. If Characters are requested for previously unseen
// strings, new Character objects are built.
//
// This class is thread-safe.
class CharacterRepository {
public:
  YCM_EXPORT static CharacterRepository &Instance();
  // Make class noncopyable
  CharacterRepository( const CharacterRepository& ) = delete;
  CharacterRepository& operator=( const CharacterRepository& ) = delete;

  YCM_EXPORT unsigned NumStoredCharacters();

  YCM_EXPORT std::vector< const Character * > GetCharactersForTexts(
    const std::vector< std::string > &texts );

  // This should only be used to isolate tests and benchmarks.
  YCM_EXPORT void ClearCharacters();

private:
  CharacterRepository() {};
  ~CharacterRepository();

  std::mutex holder_mutex_;

  static std::mutex singleton_mutex_;
  static CharacterRepository *instance_;

  const std::string empty_;

  // This data structure owns all the Character pointers
  CharacterHolder character_holder_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CHARACTER_REPOSITORY_H_36TXTS6C */
