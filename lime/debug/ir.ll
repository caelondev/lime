; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 4, i32* %".2"
  %".4" = load i32, i32* %".2"
  ret i32 %".4"
}
