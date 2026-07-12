; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

declare void @lime_print_int(i32) local_unnamed_addr

define noundef i32 @main() local_unnamed_addr {
main_entry:
  tail call void @lime_print_int(i32 0)
  tail call void @lime_print_int(i32 1)
  tail call void @lime_print_int(i32 2)
  tail call void @lime_print_int(i32 3)
  tail call void @lime_print_int(i32 4)
  tail call void @lime_print_int(i32 5)
  tail call void @lime_print_int(i32 6)
  tail call void @lime_print_int(i32 7)
  tail call void @lime_print_int(i32 8)
  tail call void @lime_print_int(i32 9)
  ret i32 0
}
