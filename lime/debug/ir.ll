; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = add i32 5, 19
  %".3" = sdiv i32 %".2", 6
  %".4" = sub i32 58, 1
  %".5" = mul i32 %".3", %".4"
  %".6" = add i32 %".5", 6
  ret i32 0
}
