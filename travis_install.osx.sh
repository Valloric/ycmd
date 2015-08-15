# OSX-specific installation

# there's a homebrew bug which causes brew update to fail the first time. run
# it twice to workaround. https://github.com/Homebrew/homebrew/issues/42553
brew update || brew update
brew install mono || brew outdated mono || brew upgrade mono
brew install node.js || brew outdated node.js || brew upgrade node.js
brew install go || brew outdated go || brew upgrade go

# OS X comes with 2 versions of python by default, and a neat system
# (versioner) to swtich:
#   /usr/bin/python2.7 - python 2.7
#   /usr/bin/python2.6 - python 2.6
#
# we just set the system default to match it
# http://stackoverflow.com/questions/6998545/how-can-i-make-python-2-6-my-default-in-mac-os-x-lion
defaults write com.apple.versioner.python Version ${YCMD_PYTHON_VERSION}

easy_install=easy_install-${YCMD_PYTHON_VERSION}
