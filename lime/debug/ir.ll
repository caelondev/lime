; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

declare void @"lime_print_int"(i32 %".1")

declare void @"lime_print_float"(double %".1")

declare void @"lime_print_bool"(i32 %".1")

declare void @"lime_print_str"(i64 %".1", i8* %".2")

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"add"(i32 1, i32 1)
  call void @"lime_print_int"(i32 %".2")
  ret i32 0
}

define i32 @"add"(i32 %".1", i32 %".2")
{
add_entry:
  %".4" = alloca i32
  store i32 %".1", i32* %".4"
  %".6" = alloca i32
  store i32 %".2", i32* %".6"
  %".8" = load i32, i32* %".4"
  %".9" = load i32, i32* %".6"
  %".10" = add i32 %".8", %".9"
  ret i32 %".10"
}
