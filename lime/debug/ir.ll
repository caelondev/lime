; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i1
  store i1 1, i1* %".2"
  %".4" = alloca i1
  store i1 0, i1* %".4"
  ret i32 0
}
