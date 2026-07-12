	.file	"<string>"
	.text
	.globl	main                            // -- Begin function main
	.p2align	2
	.type	main,@function
main:                                   // @main
	.cfi_startproc
// %bb.0:                               // %streq_merge.endif
	str	x30, [sp, #-16]!                // 8-byte Folded Spill
	.cfi_def_cfa_offset 16
	.cfi_offset w30, -16
	adrp	x1, __str_4
	add	x1, x1, :lo12:__str_4
	mov	w0, #20                         // =0x14
	bl	lime_print_str
	adrp	x1, __str_1
	add	x1, x1, :lo12:__str_1
	mov	w0, #5                          // =0x5
	bl	lime_print_str
	mov	w0, wzr
	ldr	x30, [sp], #16                  // 8-byte Folded Reload
	ret
.Lfunc_end0:
	.size	main, .Lfunc_end0-main
	.cfi_endproc
                                        // -- End function
	.type	__str_1,@object                 // @__str_1
	.section	.rodata,"a",@progbits
	.p2align	2, 0x0
__str_1:
	.ascii	"hello"
	.size	__str_1, 5

	.type	__str_4,@object                 // @__str_4
	.p2align	4, 0x0
__str_4:
	.ascii	"ITS A FUCKING STRING"
	.size	__str_4, 20

	.section	".note.GNU-stack","",@progbits
