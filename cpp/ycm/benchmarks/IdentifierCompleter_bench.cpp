// Copyright (C) 2017 ycmd contributors
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

#include "benchmark/benchmark_api.h"
#include "IdentifierCompleter.h"
#include <iomanip>
#include <sstream>

namespace YouCompleteMe {

static void IdentifierCompleter_CandidatesWithCommonPrefix_bench(
    benchmark::State& state ) {

  // Generate a list of candidates of the form a_a_a_[a-z]{5}.
  std::vector< std::string > candidates;
  for ( int i = 0; i < state.range( 0 ); i++ ) {
    std::string candidate = "a_a_a_";
    std::ostringstream number;
    number << std::setfill( '0' ) << std::setw( 5 ) << i;
    for ( auto character : number.str() ) {
      candidate += character - '0' + 'a';
    }
    candidates.push_back( candidate );
  }

  while ( state.KeepRunning() )
    IdentifierCompleter( candidates ).CandidatesForQuery( "aa" );

  state.SetComplexityN( state.range(0) );
}

BENCHMARK( IdentifierCompleter_CandidatesWithCommonPrefix_bench )
    ->RangeMultiplier( 2 )
    ->Range( 1, 1 << 16 )
    ->Complexity();

} // namespace YouCompleteMe
