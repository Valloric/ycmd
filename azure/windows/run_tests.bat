:: Add Python to PATH
set "PATH=C:\Python;C:\Python\Scripts;%PATH%"
:: Add the MSBuild executable to PATH
set "PATH=%MSBUILD_PATH%;%PATH%"
:: Add the Cargo executable to PATH
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
:: Add the Go executable to PATH
set "PATH=C:\Go\bin;%PATH%"

:: Prevent the already installed version of Go to conflict with ours.
set GOROOT=

python run_tests.py --msvc %MSVC%
