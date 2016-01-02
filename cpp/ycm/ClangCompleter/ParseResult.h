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

#ifndef PARSERESULT_H_9T5FNJAS
#define PARSERESULT_H_9T5FNJAS

#include "Diagnostic.h"
#include "Token.h"

#include <vector>

namespace YouCompleteMe {

struct ParseResult {
        typedef std::vector< Diagnostic > Diagnostics;

        typedef std::vector< Token > Semantics;

        ParseResult() : diagnostics_(), semantics_() {}

        Diagnostics diagnostics_;

        Semantics semantics_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: PARSERESULT_H_9T5FNJAS */
