; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 1, i32* %".2"
  %".4" = load i32, i32* %".2"
  %".5" = load i32, i32* %".2"
  %".6" = icmp eq i32 %".4", %".5"
  %".7" = alloca i1
  store i1 %".6", i1* %".7"
  ret i32 0
}
