; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

declare void @lime_print_int(i32) local_unnamed_addr

declare i32 @add(i32, i32) local_unnamed_addr

define noundef i32 @main() local_unnamed_addr {
main_entry:
  %.2 = tail call i32 @add(i32 60, i32 7)
  tail call void @lime_print_int(i32 %.2)
  ret i32 0
}
