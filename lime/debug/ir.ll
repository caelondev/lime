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
  %".2" = getelementptr inbounds [4 x i8], [4 x i8]* @"__str_1", i32 0, i32 0
  %".3" = insertvalue {i64, i8*} undef, i64 4, 0
  %".4" = insertvalue {i64, i8*} %".3", i8* %".2", 1
  %".5" = alloca {i64, i8*}
  store {i64, i8*} %".4", {i64, i8*}* %".5"
  %".7" = load {i64, i8*}, {i64, i8*}* %".5"
  %".8" = extractvalue {i64, i8*} %".7", 0
  %".9" = extractvalue {i64, i8*} %".7", 1
  call void @"lime_print_str"(i64 %".8", i8* %".9")
  call void @"lime_print_int"(i32 0)
  ret i32 0
}

@"__str_1" = internal constant [4 x i8] c"true"