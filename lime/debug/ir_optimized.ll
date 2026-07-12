; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

declare void @lime_print_int(i32) local_unnamed_addr

define noundef i32 @main() local_unnamed_addr {
main_entry:
  tail call void @lime_print_int(i32 2)
  ret i32 0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define i32 @add(i32 %.1, i32 %.2) local_unnamed_addr #0 {
add_entry:
  %.10 = add i32 %.2, %.1
  ret i32 %.10
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) }
