; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

@__str_1 = internal constant [4 x i8] c"true"

declare void @lime_print_int(i32) local_unnamed_addr

declare void @lime_print_str(i64, ptr) local_unnamed_addr

define noundef i32 @main() local_unnamed_addr {
main_entry:
  tail call void @lime_print_str(i64 4, ptr nonnull @__str_1)
  tail call void @lime_print_int(i32 0)
  ret i32 0
}
