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
  %".2" = alloca i32
  store i32 0, i32* %".2"
  br label %"while.cond.1"
while.cond.1:
  %".5" = load i32, i32* %".2"
  %".6" = icmp slt i32 %".5", 10
  br i1 %".6", label %"while.body.1", label %"while.end.1"
while.body.1:
  %".8" = load i32, i32* %".2"
  call void @"lime_print_int"(i32 %".8")
  %".10" = load i32, i32* %".2"
  %".11" = add i32 %".10", 1
  store i32 %".11", i32* %".2"
  br label %"while.cond.1"
while.end.1:
  ret i32 0
}
