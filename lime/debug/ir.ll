; ModuleID = "main"
target triple = "aarch64-unknown-linux-android24"
target datalayout = ""

define i32 @"ret"()
{
ret_entry:
  %".2" = alloca i32
  store i32 10, i32* %".2"
  %".4" = alloca i32
  store i32 20, i32* %".4"
  %".6" = load i32, i32* %".2"
  %".7" = add i32 %".6", 5
  store i32 %".7", i32* %".2"
  %".9" = load i32, i32* %".2"
  ret i32 %".9"
}

define i32 @"square_of_ret"()
{
square_of_ret_entry:
  %".2" = call i32 @"ret"()
  %".3" = alloca i32
  store i32 %".2", i32* %".3"
  %".5" = load i32, i32* %".3"
  %".6" = load i32, i32* %".3"
  %".7" = mul i32 %".5", %".6"
  ret i32 %".7"
}

define i1 @"is_even_check"()
{
is_even_check_entry:
  %".2" = call i32 @"ret"()
  %".3" = alloca i32
  store i32 %".2", i32* %".3"
  %".5" = load i32, i32* %".3"
  %".6" = srem i32 %".5", 2
  %".7" = icmp eq i32 %".6", 0
  ret i1 %".7"
}

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"ret"()
  %".3" = alloca i32
  store i32 %".2", i32* %".3"
  %".5" = call i32 @"square_of_ret"()
  %".6" = alloca i32
  store i32 %".5", i32* %".6"
  %".8" = call i1 @"is_even_check"()
  %".9" = alloca i1
  store i1 %".8", i1* %".9"
  %".11" = load i1, i1* %".9"
  br i1 %".11", label %"main_entry.if", label %"main_entry.else"
main_entry.if:
  %".13" = load i32, i32* %".6"
  %".14" = load i32, i32* %".3"
  %".15" = sub i32 %".13", %".14"
  ret i32 %".15"
main_entry.else:
  %".17" = load i32, i32* %".3"
  ret i32 %".17"
main_entry.endif:
  unreachable
}
