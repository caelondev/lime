; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 2, i32* %".2"
  %".4" = load i32, i32* %".2"
  %".5" = icmp eq i32 %".4", 1
  br i1 %".5", label %"main_entry.if", label %"main_entry.else"
main_entry.if:
  store i32 0, i32* %".2"
  br label %"main_entry.endif"
main_entry.else:
  %".9" = load i32, i32* %".2"
  %".10" = icmp eq i32 %".9", 2
  br i1 %".10", label %"main_entry.else.if", label %"main_entry.else.else"
main_entry.endif:
  %".17" = load i32, i32* %".2"
  ret i32 %".17"
main_entry.else.if:
  store i32 1, i32* %".2"
  ret i32 2
main_entry.else.else:
  store i32 2, i32* %".2"
  br label %"main_entry.else.endif"
main_entry.else.endif:
  br label %"main_entry.endif"
}
