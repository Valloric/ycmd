if [ "${YCM_BENCHMARK}" == "true" ]; then
  ./benchmark.py
elif [ "${YCM_CLANG_TIDY}" == "true" ]; then
  ./build.py --clang-completer --clang-tidy --quiet
else
  ./run_tests.py
fi
