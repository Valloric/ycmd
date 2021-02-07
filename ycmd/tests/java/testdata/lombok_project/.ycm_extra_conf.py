import os

PATH_TO_LOMBOK = os.path.expanduser(
  '~/.gradle/caches/modules-2/files-2.1/org.projectlombok/lombok/' +
  '1.18.16/6dc192c7f93ec1853f70d59d8a6dcf94eb42866/lombok-1.18.16.jar' )


def Settings( **kwargs ):
  if not os.path.exists( PATH_TO_LOMBOK ):
    raise RuntimeError( "No lombok jar located at " + PATH_TO_LOMBOK )

  jvm_args = [
    '-noverify',
    '-Xmx1G',
    '-XX:+UseG1GC',
    '-XX:+UseStringDeduplication',
  ]

  return {
    'server': {
      'jvm_args': [ '-javaagent:' + PATH_TO_LOMBOK ] + jvm_args
    }
  }
