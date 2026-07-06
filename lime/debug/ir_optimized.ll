; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i32 @ret() local_unnamed_addr #0 {
ret_entry:
  ret i32 15
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i32 @square_of_ret() local_unnamed_addr #0 {
square_of_ret_entry:
  ret i32 225
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i1 @is_even_check() local_unnamed_addr #0 {
is_even_check_entry:
  ret i1 false
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i32 @main() local_unnamed_addr #0 {
main_entry:
  ret i32 15
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) }
