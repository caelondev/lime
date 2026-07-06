; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 5, i32* %".2"
  %".4" = alloca i32
  store i32 0, i32* %".4"
  store i32 3, i32* %".4"
  store i32 3, i32* %".2"
  %".8" = load i32, i32* %".2"
  ret i32 %".8"
}
