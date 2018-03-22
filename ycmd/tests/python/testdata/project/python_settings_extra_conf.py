import os

DIR_OF_THIS_SCRIPT = os.path.abspath( os.path.dirname( __file__ ) )


def PythonSettings( **kwargs ):
  return {
    'sys_path': [ os.path.join( DIR_OF_THIS_SCRIPT, 'third_party' ) ]
  }
