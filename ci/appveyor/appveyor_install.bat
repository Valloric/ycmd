git submodule update --init --recursive
:: Batch script will not exit if a command returns an error, so we manually do
:: it for commands that may fail.
if %errorlevel% neq 0 exit /b %errorlevel%

::
:: Python configuration
::

if %arch% == 32 (
  set python_path=C:\Python%python%
) else (
  set python_path=C:\Python%python%-x64
)

set PATH=%python_path%;%python_path%\Scripts;%PATH%
python --version

appveyor DownloadFile https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install -r test_requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%
pip install codecov
if %errorlevel% neq 0 exit /b %errorlevel%
del get-pip.py

:: Enable coverage for Python subprocesses. See:
:: http://coverage.readthedocs.io/en/latest/subprocess.html
python -c "with open('%python_path%\Lib\site-packages\sitecustomize.py', 'w') as f: f.write('import coverage\ncoverage.process_startup()')"

::
:: Java Configuration (Java 8 required for jdt.ls)
::
if %arch% == 32 (
  set "JAVA_HOME=C:\Program Files (x86)\Java\jdk1.8.0"
) else (
  set "JAVA_HOME=C:\Program Files\Java\jdk1.8.0"
)

set PATH=%JAVA_HOME%\bin;%PATH%
java -version
