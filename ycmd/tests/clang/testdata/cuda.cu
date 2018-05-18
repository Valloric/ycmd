#include "cuda.h"

__global__ void noopKernel() {}

int main(int argc, char *argv[])
{
  noopKernel<<<1, 1>>>();
  return 0;
}
