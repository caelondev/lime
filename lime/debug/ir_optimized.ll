; ModuleID = '<string>'
source_filename = "<string>"
target triple = "aarch64-unknown-linux-android24"

; Function Attrs: nofree nosync nounwind memory(none)
define i32 @fib(i32 %.1) local_unnamed_addr #0 {
fib_entry:
  %.64 = icmp slt i32 %.1, 2
  br i1 %.64, label %common.ret, label %fib_entry.endif

common.ret:                                       ; preds = %fib_entry.endif, %fib_entry
  %accumulator.tr.lcssa = phi i32 [ 0, %fib_entry ], [ %.16, %fib_entry.endif ]
  %.1.tr.lcssa = phi i32 [ %.1, %fib_entry ], [ 1, %fib_entry.endif ]
  %accumulator.ret.tr = add i32 %.1.tr.lcssa, %accumulator.tr.lcssa
  ret i32 %accumulator.ret.tr

fib_entry.endif:                                  ; preds = %fib_entry, %fib_entry.endif
  %.1.tr6 = phi i32 [ %.14, %fib_entry.endif ], [ %.1, %fib_entry ]
  %accumulator.tr5 = phi i32 [ %.16, %fib_entry.endif ], [ 0, %fib_entry ]
  %.11 = add nsw i32 %.1.tr6, -2
  %.12 = tail call i32 @fib(i32 %.11)
  %.14 = add nsw i32 %.1.tr6, -1
  %.16 = add i32 %.12, %accumulator.tr5
  %.6 = icmp samesign ult i32 %.1.tr6, 3
  br i1 %.6, label %common.ret, label %fib_entry.endif
}

; Function Attrs: nofree nosync nounwind memory(none)
define i32 @main() local_unnamed_addr #0 {
main_entry:
  %.2 = tail call i32 @fib(i32 20)
  ret i32 %.2
}

attributes #0 = { nofree nosync nounwind memory(none) }
