#include <stdint.h>
#include <stdio.h>

int32_t add(int32_t a, int32_t b) { return a + b; }

void lime_print_int(int32_t x) { printf("%d\n", x); }
void lime_print_float(double x) { printf("%f\n", x); }
void lime_print_bool(int32_t b) { printf("%s\n", b ? "true" : "false"); }
void lime_print_str(int64_t len, const char *data) {
  fwrite(data, 1, (size_t)len, stdout);
  putchar('\n');
}
