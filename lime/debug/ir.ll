; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

declare i32 @"printf"(i8* %".fmt", ...)

@".fstr" = private unnamed_addr constant [4 x i8] c"%d\0A\00"

define i32 @"fib"(i32 %".1")
{
fib_entry:
  %".3" = alloca i32
  store i32 %".1", i32* %".3"
  %".5" = load i32, i32* %".3"
  %".6" = icmp sle i32 %".5", 1
  br i1 %".6", label %"fib_entry.if", label %"fib_entry.endif"
fib_entry.if:
  %".8" = load i32, i32* %".3"
  ret i32 %".8"
fib_entry.endif:
  %".10" = load i32, i32* %".3"
  %".11" = sub i32 %".10", 2
  %".12" = call i32 @"fib"(i32 %".11")
  %".13" = load i32, i32* %".3"
  %".14" = sub i32 %".13", 1
  %".15" = call i32 @"fib"(i32 %".14")
  %".16" = add i32 %".12", %".15"
  ret i32 %".16"
}

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"fib"(i32 20)
  %".20" = getelementptr [4 x i8], [4 x i8]* @".fstr", i32 0, i32 0
  %".21" = call i32 (i8*, ...) @"printf"(i8* %".20", i32 %".2")
  ret i32 0
}
