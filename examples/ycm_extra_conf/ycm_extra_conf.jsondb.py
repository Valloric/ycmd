import os
import fnmatch
import re
import ycm_core
import json
import itertools

flags = []

# Set this to the absolute path to the folder (NOT the file!) containing the
# compile_commands.json file to use that instead of 'flags'. See here for
# more details: http://clang.llvm.org/docs/JSONCompilationDatabase.html
compilation_database_folder = 'build/osx_x64_debug/make'

if os.path.exists( compilation_database_folder ):
  database = ycm_core.CompilationDatabase( compilation_database_folder )
else:
  database = None

SOURCE_EXTENSIONS = [ '.cpp', '.cxx', '.cc', '.c', '.m', '.mm' ]

def DirectoryOfThisScript():
  return os.path.dirname( os.path.abspath( __file__ ) )


def MakeRelativePathsInFlagsAbsolute( flags, working_directory ):
  if not working_directory:
    return list( flags )
  new_flags = []
  make_next_absolute = False
  path_flags = [ '-isystem', '-I', '-iquote', '--sysroot=' ]
  for flag in flags:
    new_flag = flag

    if make_next_absolute:
      make_next_absolute = False
      if not flag.startswith( '/' ):
        new_flag = os.path.join( working_directory, flag )

    for path_flag in path_flags:
      if flag == path_flag:
        make_next_absolute = True
        break

      if flag.startswith( path_flag ):
        path = flag[ len( path_flag ): ]
        new_flag = path_flag + os.path.join( working_directory, path )
        break

    if new_flag:
      new_flags.append( new_flag )
  return new_flags


def IsHeaderFile( filename ):
  extension = os.path.splitext( filename )[ 1 ]
  return extension in [ '.h', '.hxx', '.hpp', '.hh' ]


def pairwise(iterable):
  "s -> (s0,s1), (s1,s2), (s2, s3), ..."
  a, b = itertools.tee(iterable)
  next(b, None)
  return itertools.izip(a, b)


def removeClosingSlash(path):
  if path.endswith('/'):
    path = path[:-1]
  return path


def searchForTranslationUnitWhichIncludesPath(compileCommandsPath, path):
  path = removeClosingSlash(path)
  m = re.match( r'(.*/include)', path)
  if m:
    path = m.group(1)
  jsonData = open(compileCommandsPath)
  data = json.load(jsonData)
  for translationUnit in data:
    print translationUnit["command"]
    switches = translationUnit["command"].split()
    for currentSwitch, nextSwitch in pairwise(switches):
      matchObj = re.match( r'(-I|-isystem)(.*)', currentSwitch)
      includeDir = ""
      if currentSwitch == "-I" or currentSwitch == "-isystem":
        includeDir = nextSwitch
      elif matchObj:
        includeDir = matchObj.group(2)
      includeDir = removeClosingSlash(includeDir)
      if includeDir == path:
        print "Found " + translationUnit["file"]
        # TODO finally
        jsonData.close()
        return str(translationUnit["file"])
  jsonData.close()
  return None


def GetCompilationInfoForFile( filename ):
  print "GetCompilationInfoForFile: filename: " + filename
  # The compilation_commands.json file generated by CMake does not have entries
  # for header files. So we do our best by asking the db for flags for a
  # corresponding source file, if any. If one exists, the flags for that file
  # should be good enough.
  if IsHeaderFile( filename ):
    basename = os.path.splitext( filename )[ 0 ]
    for extension in SOURCE_EXTENSIONS:
      replacement_file = basename + extension
      if os.path.exists( replacement_file ):
        print "Matching src file, based on method0: " + replacement_file
        compilation_info = database.GetCompilationInfoForFile(
          replacement_file )
        if compilation_info.compiler_flags_:
          return compilation_info

    # If still not found a candidate translation unit,
    # then try to browse the json db to find one,
    # which uses the directory of our header as an include path (-I, -isystem).
    basename = os.path.split( filename ) [ 1 ]
    dirname = os.path.dirname( filename )
    compilation_database_file = compilation_database_folder + "/" + "compile_commands.json"
    candidateSrcFile = searchForTranslationUnitWhichIncludesPath(compilation_database_file, dirname)
    if candidateSrcFile != None:
      print "Matching src file, based on method1: " + candidateSrcFile
      return database.GetCompilationInfoForFile(candidateSrcFile)

  return database.GetCompilationInfoForFile( filename )


def FlagsForFile( filename, **kwargs ):
  if database:
    # Bear in mind that compilation_info.compiler_flags_ does NOT return a
    # python list, but a "list-like" StringVec object
    compilation_info = GetCompilationInfoForFile( filename )
    if not compilation_info:
      return None

    final_flags = MakeRelativePathsInFlagsAbsolute(
      compilation_info.compiler_flags_,
      compilation_info.compiler_working_dir_ )

    # NOTE: This is just for YouCompleteMe; it's highly likely that your project
    # does NOT need to remove the stdlib flag. DO NOT USE THIS IN YOUR
    # ycm_extra_conf IF YOU'RE NOT 100% SURE YOU NEED IT.
    try:
      #final_flags.remove( '-stdlib=libc++' )
      final_flags.append('-isystem')
      final_flags.append('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/../lib/c++/v1')
      final_flags.append('-isystem')
      final_flags.append('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include')
      final_flags.append('-isystem')
      final_flags.append('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/../lib/clang/5.1/include')
      final_flags.append('-isystem')
      final_flags.append('/usr/include')
      final_flags.append('-isystem')
      final_flags.append('/usr/local/include')

    except ValueError:
      pass
  else:
    relative_to = DirectoryOfThisScript()
    final_flags = MakeRelativePathsInFlagsAbsolute( flags, relative_to )

  return {
    'flags': final_flags,
    'do_cache': True
  }
