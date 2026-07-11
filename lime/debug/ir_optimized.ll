; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

@__str_2 = internal constant [6 x i8] c"string"

declare void @lime_print_str(i64, ptr) local_unnamed_addr

define noundef i32 @main() local_unnamed_addr {
main_entry:
  tail call void @lime_print_str(i64 6, ptr nonnull @__str_2)
  ret i32 0
}
