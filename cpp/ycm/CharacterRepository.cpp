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

#include "CharacterRepository.h"
#include "Character.h"
#include "Utils.h"

#include <mutex>

namespace YouCompleteMe {

std::mutex CharacterRepository::singleton_mutex_;
CharacterRepository *CharacterRepository::instance_ = NULL;

CharacterRepository &CharacterRepository::Instance() {
  std::lock_guard< std::mutex > locker( singleton_mutex_ );

  if ( !instance_ ) {
    static CharacterRepository repo;
    instance_ = &repo;
  }

  return *instance_;
}


unsigned CharacterRepository::NumStoredCharacters() {
  std::lock_guard< std::mutex > locker( holder_mutex_ );
  return character_holder_.size();
}


std::vector< const Character * > CharacterRepository::GetCharactersForTexts(
  const std::vector< std::string > &texts ) {
  std::vector< const Character * > characters;
  characters.reserve( texts.size() );

  {
    std::lock_guard< std::mutex > locker( holder_mutex_ );

    for ( const std::string & text : texts ) {
      const Character *&character = GetValueElseInsert(
                                      character_holder_,
                                      text,
                                      NULL );

      if ( !character )
        character = new Character( text );

      characters.push_back( character );
    }
  }

  return characters;
}


void CharacterRepository::ClearCharacters() {
  for ( const CharacterHolder::value_type & pair : character_holder_ ) {
    delete pair.second;
  }
  character_holder_.clear();
}


CharacterRepository::~CharacterRepository() {
  for ( const CharacterHolder::value_type & pair : character_holder_ ) {
    delete pair.second;
  }
}


} // namespace YouCompleteMe
