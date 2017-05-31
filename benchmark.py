#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import os.path as p
import subprocess
import sys

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.join( DIR_OF_THIS_SCRIPT, 'third_party' )

sys.path.insert( 1, p.abspath( p.join( DIR_OF_THIRD_PARTY, 'argparse' ) ) )

import argparse


def ParseArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '--msvc', type = int, choices = [ 12, 14, 15 ],
                       help = 'Choose the Microsoft Visual '
                       'Studio version. (default: 15).' )

  return parser.parse_args()


def BuildYcmdLibsAndRunBenchmark( args ):
  build_cmd = [
    sys.executable,
    p.join( DIR_OF_THIS_SCRIPT, 'build.py' ),
    '--clang-completer'
  ]

  os.environ[ 'YCM_BENCHMARK' ] = '1'

  if args.msvc:
    build_cmd.extend( [ '--msvc', str( args.msvc ) ] )

  subprocess.check_call( build_cmd )


def Main():
  args = ParseArguments()
  BuildYcmdLibsAndRunBenchmark( args )


if __name__ == "__main__":
  Main()
