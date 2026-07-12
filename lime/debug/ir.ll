; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

declare void @"lime_print_int"(i32 %".1")

declare void @"lime_print_float"(double %".1")

declare void @"lime_print_bool"(i32 %".1")

declare void @"lime_print_str"(i64 %".1", i8* %".2")

declare i32 @"add"(i32 %".1", i32 %".2")

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"add"(i32 60, i32 7)
  call void @"lime_print_int"(i32 %".2")
  ret i32 0
}
