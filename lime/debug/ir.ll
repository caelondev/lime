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
  %".2" = getelementptr inbounds [0 x i8], [0 x i8]* @"__str_1", i32 0, i32 0
  %".3" = insertvalue {i64, i8*} undef, i64 0, 0
  %".4" = insertvalue {i64, i8*} %".3", i8* %".2", 1
  %".5" = getelementptr inbounds [6 x i8], [6 x i8]* @"__str_2", i32 0, i32 0
  %".6" = insertvalue {i64, i8*} undef, i64 6, 0
  %".7" = insertvalue {i64, i8*} %".6", i8* %".5", 1
  %".8" = extractvalue {i64, i8*} %".7", 0
  %".9" = extractvalue {i64, i8*} %".7", 1
  call void @"lime_print_str"(i64 %".8", i8* %".9")
  ret i32 0
}

@"__str_1" = internal constant [0 x i8] c""
@"__str_2" = internal constant [6 x i8] c"string"