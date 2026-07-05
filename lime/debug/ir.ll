; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = fmul float 0x4011000000000000, 0x401c000000000000
  %".3" = frem float %".2", 0x4000000000000000
  ret i32 0
}
