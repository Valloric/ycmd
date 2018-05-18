#include "cuda.h"

__global__ void noopKernel() {}

int main(void) {
  noopKernel<<<1, 1>>>();
  return 0;
}
