#! /usr/bin/env python3

"""
TL;DR scrape felixs' website for all the instructions and their descriptions.
The mechanical extraction of data results in inconsitencies that is annoying to
write an extraction script for. So I just threw an LLM at it...
It mostly works, and costs like $2 for the whole run which is worth it for me.
"""

from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
import hashlib
import os
import requests
import time

BASE_URL = "https://www.felixcloutier.com/x86/"

BASE_PROMT = """You are an expert in HTML and X86 assembly.
You will be provided with the HTML of a page that contains a table of instructions and their descriptions.
Your job is to extract all the unique instructions mnemonics, their descriptions, and a brief summary of the instruction.

<instructions>
1. Extract all unique instructions mnemonics from the table and their descriptions.
2. Extract the description of the page from the paragraphs below the table. Ignore figures and tables, or summarize them if they are relevant to the instructions.
3. Use the exact format of the example below to format your output.
</instructions>

<example>
<input>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:svg="http://www.w3.org/2000/svg" xmlns:x86="http://www.felixcloutier.com/x86"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><link rel="stylesheet" type="text/css" href="style.css"></link><title>VCVTPH2PS/VCVTPH2PSX
		— Convert Packed FP16 Values to Single Precision Floating-PointValues</title></head><body><header><nav><ul><li><a href='/x86/'>Index</a></li><li>December 2023</li></ul></nav></header><h1>VCVTPH2PS/VCVTPH2PSX
		— Convert Packed FP16 Values to Single Precision Floating-PointValues</h1>


<table>
<tr>
<th>Opcode/Instruction</th>
<th>Op / En</th>
<th>64/32 Bit Mode Support</th>
<th>CPUID Feature Flag</th>
<th>Description</th></tr>
<tr>
<td>VEX.128.66.0F38.W0 13 /r VCVTPH2PS xmm1, xmm2/m64</td>
<td>A</td>
<td>V/V</td>
<td>F16C</td>
<td>Convert four packed FP16 values in xmm2/m64 to packed single precision floating-point value in xmm1.</td></tr>
<tr>
<td>VEX.256.66.0F38.W0 13 /r VCVTPH2PS ymm1, xmm2/m128</td>
<td>A</td>
<td>V/V</td>
<td>F16C</td>
<td>Convert eight packed FP16 values in xmm2/m128 to packed single precision floating-point value in ymm1.</td></tr>
<tr>
<td>EVEX.128.66.0F38.W0 13 /r VCVTPH2PS xmm1 {k1}{z}, xmm2/m64</td>
<td>B</td>
<td>V/V</td>
<td>AVX512VL AVX512F</td>
<td>Convert four packed FP16 values in xmm2/m64 to packed single precision floating-point values in xmm1 subject to writemask k1.</td></tr>
<tr>
<td>EVEX.256.66.0F38.W0 13 /r VCVTPH2PS ymm1 {k1}{z}, xmm2/m128</td>
<td>B</td>
<td>V/V</td>
<td>AVX512VL AVX512F</td>
<td>Convert eight packed FP16 values in xmm2/m128 to packed single precision floating-point values in ymm1 subject to writemask k1.</td></tr>
<tr>
<td>EVEX.512.66.0F38.W0 13 /r VCVTPH2PS zmm1 {k1}{z}, ymm2/m256 {sae}</td>
<td>B</td>
<td>V/V</td>
<td>AVX512F</td>
<td>Convert sixteen packed FP16 values in ymm2/m256 to packed single precision floating-point values in zmm1 subject to writemask k1.</td></tr>
<tr>
<td>EVEX.128.66.MAP6.W0 13 /r VCVTPH2PSX xmm1{k1}{z}, xmm2/m64/m16bcst</td>
<td>C</td>
<td>V/V</td>
<td>AVX512-FP16 AVX512VL</td>
<td>Convert four packed FP16 values in xmm2/m64/m16bcst to four packed single precision floating-point values, and store result in xmm1 subject to writemask k1.</td></tr>
<tr>
<td>EVEX.256.66.MAP6.W0 13 /r VCVTPH2PSX ymm1{k1}{z}, xmm2/m128/m16bcst</td>
<td>C</td>
<td>V/V</td>
<td>AVX512-FP16 AVX512VL</td>
<td>Convert eight packed FP16 values in xmm2/m128/m16bcst to eight packed single precision floating-point values, and store result in ymm1 subject to writemask k1.</td></tr>
<tr>
<td>EVEX.512.66.MAP6.W0 13 /r VCVTPH2PSX zmm1{k1}{z}, ymm2/m256/m16bcst {sae}</td>
<td>C</td>
<td>V/V</td>
<td>AVX512-FP16</td>
<td>Convert sixteen packed FP16 values in ymm2/m256/m16bcst to sixteen packed single precision floating-point values, and store result in zmm1 subject to writemask k1.</td></tr></table>
<h2 id="instruction-operand-encoding">Instruction Operand Encoding<a class="anchor" href="#instruction-operand-encoding">
			¶
		</a></h2>
<table>
<tr>
<th>Op/En</th>
<th>Tuple Type</th>
<th>Operand 1</th>
<th>Operand 2</th>
<th>Operand 3</th>
<th>Operand 4</th></tr>
<tr>
<td>A</td>
<td>N/A</td>
<td>ModRM:reg (w)</td>
<td>ModRM:r/m (r)</td>
<td>N/A</td>
<td>N/A</td></tr>
<tr>
<td>B</td>
<td>Half Mem</td>
<td>ModRM:reg (w)</td>
<td>ModRM:r/m (r)</td>
<td>N/A</td>
<td>N/A</td></tr>
<tr>
<td>C</td>
<td>Half</td>
<td>ModRM:reg (w)</td>
<td>ModRM:r/m (r)</td>
<td>N/A</td>
<td>N/A</td></tr></table>
<h3 id="description">Description<a class="anchor" href="#description">
			¶
		</a></h3>
<p>This instruction converts packed half precision (16-bits) floating-point values in the low-order bits of the source operand (the second operand) to packed single precision floating-point values and writes the converted values into the destination operand (the first operand).</p>
<p>If case of a denormal operand, the correct normal result is returned. MXCSR.DAZ is ignored and is treated as if it 0. No denormal exception is reported on MXCSR.</p>
<p>VEX.128 version: The source operand is a XMM register or 64-bit memory location. The destination operand is a XMM register. The upper bits (MAXVL-1:128) of the corresponding destination register are zeroed.</p>
<p>VEX.256 version: The source operand is a XMM register or 128-bit memory location. The destination operand is a YMM register. Bits (MAXVL-1:256) of the corresponding destination register are zeroed.</p>
<p>EVEX encoded versions: The source operand is a YMM/XMM/XMM (low 64-bits) register or a 256/128/64-bit memory location. The destination operand is a ZMM/YMM/XMM register conditionally updated with writemask k1.</p>
<p>The diagram below illustrates how data is converted from four packed half precision (in 64 bits) to four single precision (in 128 bits) floating-point values.</p>
<p>Note: VEX.vvvv and EVEX.vvvv are reserved (must be 1111b).</p>
<figure id="fig-5-6">
<table>
<tr>
<td>VCVTPH2PS<em>xmm1,xmm2/mem64, imm8</em> 127 96 95 64 63 48 47 32 31 16 15 0</td></tr>
<tr>
<td>xmm2/mem64 VH3 VH2 VH1 VH0</td></tr>
<tr>
<td rowspan="4">convert convert convert convert 127 96 95 64 63 32 31 0</td></tr>
<tr>
<td>VS3 VS2 VS1 VS0 xmm1</td></tr></table>
<figcaption><a href='/x86/vcvtph2ps:vcvtph2psx#fig-5-6'>Figure 5-6</a>. VCVTPH2PS (128-bit Version)</figcaption></figure>
<p>The VCVTPH2PSX instruction is a new form of the PH to PS conversion instruction, encoded in map 6. The previous version of the instruction, VCVTPH2PS, that is present in AVX512F (encoded in map 2, 0F38) does not support embedded broadcasting. The VCVTPH2PSX instruction has the embedded broadcasting option available.</p>
<p>The instructions associated with AVX512_FP16 always handle FP16 denormal number inputs; denormal inputs are not treated as zero.</p>
<h3 id="operation">Operation<a class="anchor" href="#operation">
			¶
		</a></h3>
<pre>vCvt_h2s(SRC1[15:0])
{
RETURN Cvt_Half_Precision_To_Single_Precision(SRC1[15:0]);
}
</pre>
<h4 id="vcvtph2ps--evex-encoded-versions-">VCVTPH2PS (EVEX Encoded Versions)<a class="anchor" href="#vcvtph2ps--evex-encoded-versions-">
			¶
		</a></h4>
<pre>(KL, VL) = (4, 128), (8, 256), (16, 512)
FOR j := 0 TO KL-1
    i := j * 32
    k := j * 16
    IF k1[j] OR *no writemask*
        THEN DEST[i+31:i] :=
            vCvt_h2s(SRC[k+15:k])
        ELSE
            IF *merging-masking*
                        ; merging-masking
                THEN *DEST[i+31:i] remains unchanged*
                ELSE
                        ; zeroing-masking
                    DEST[i+31:i] := 0
            FI
    FI;
ENDFOR
DEST[MAXVL-1:VL] := 0
</pre>
<h4 id="vcvtph2ps--vex-256-encoded-version-">VCVTPH2PS (VEX.256 Encoded Version)<a class="anchor" href="#vcvtph2ps--vex-256-encoded-version-">
			¶
		</a></h4>
<pre>DEST[31:0] := vCvt_h2s(SRC1[15:0]);
DEST[63:32] := vCvt_h2s(SRC1[31:16]);
DEST[95:64] := vCvt_h2s(SRC1[47:32]);
DEST[127:96] := vCvt_h2s(SRC1[63:48]);
DEST[159:128] := vCvt_h2s(SRC1[79:64]);
DEST[191:160] := vCvt_h2s(SRC1[95:80]);
DEST[223:192] := vCvt_h2s(SRC1[111:96]);
DEST[255:224] := vCvt_h2s(SRC1[127:112]);
DEST[MAXVL-1:256] := 0
</pre>
<h4 id="vcvtph2ps--vex-128-encoded-version-">VCVTPH2PS (VEX.128 Encoded Version)<a class="anchor" href="#vcvtph2ps--vex-128-encoded-version-">
			¶
		</a></h4>
<pre>DEST[31:0] := vCvt_h2s(SRC1[15:0]);
DEST[63:32] := vCvt_h2s(SRC1[31:16]);
DEST[95:64] := vCvt_h2s(SRC1[47:32]);
DEST[127:96] := vCvt_h2s(SRC1[63:48]);
DEST[MAXVL-1:128] := 0
</pre>
<h4 id="vcvtph2psx-dest--src">VCVTPH2PSX DEST, SRC<a class="anchor" href="#vcvtph2psx-dest--src">
			¶
		</a></h4>
<pre>VL = 128, 256, or 512
KL := VL/32
FOR j := 0 TO KL-1:
    IF k1[j] OR *no writemask*:
        IF *SRC is memory* and EVEX.b = 1:
            tsrc := SRC.fp16[0]
        ELSE
            tsrc := SRC.fp16[j]
        DEST.fp32[j] := Convert_fp16_to_fp32(tsrc)
    ELSE IF *zeroing*:
        DEST.fp32[j] := 0
    // else dest.fp32[j] remains unchanged
DEST[MAXVL-1:VL] := 0
</pre>
<h3 id="flags-affected">Flags Affected<a class="anchor" href="#flags-affected">
			¶
		</a></h3>
<p>None.</p>
<h3 id="intel-c-c++-compiler-intrinsic-equivalent">Intel C/C++ Compiler Intrinsic Equivalent<a class="anchor" href="#intel-c-c++-compiler-intrinsic-equivalent">
			¶
		</a></h3>
<pre>VCVTPH2PS __m512 _mm512_cvtph_ps( __m256i a);
</pre>
<pre>VCVTPH2PS __m512 _mm512_mask_cvtph_ps(__m512 s, __mmask16 k, __m256i a);
</pre>
<pre>VCVTPH2PS __m512 _mm512_maskz_cvtph_ps(__mmask16 k, __m256i a);
</pre>
<pre>VCVTPH2PS __m512 _mm512_cvt_roundph_ps( __m256i a, int sae);
</pre>
<pre>VCVTPH2PS __m512 _mm512_mask_cvt_roundph_ps(__m512 s, __mmask16 k, __m256i a, int sae);
</pre>
<pre>VCVTPH2PS __m512 _mm512_maskz_cvt_roundph_ps( __mmask16 k, __m256i a, int sae);
</pre>
<pre>VCVTPH2PS __m256 _mm256_mask_cvtph_ps(__m256 s, __mmask8 k, __m128i a);
</pre>
<pre>VCVTPH2PS __m256 _mm256_maskz_cvtph_ps(__mmask8 k, __m128i a);
</pre>
<pre>VCVTPH2PS __m128 _mm_mask_cvtph_ps(__m128 s, __mmask8 k, __m128i a);
</pre>
<pre>VCVTPH2PS __m128 _mm_maskz_cvtph_ps(__mmask8 k, __m128i a);
</pre>
<pre>VCVTPH2PS __m128 _mm_cvtph_ps ( __m128i m1);
</pre>
<pre>VCVTPH2PS __m256 _mm256_cvtph_ps ( __m128i m1)
</pre>
<pre>VCVTPH2PSX __m512 _mm512_cvtx_roundph_ps (__m256h a, int sae);
</pre>
<pre>VCVTPH2PSX __m512 _mm512_mask_cvtx_roundph_ps (__m512 src, __mmask16 k, __m256h a, int sae);
</pre>
<pre>VCVTPH2PSX __m512 _mm512_maskz_cvtx_roundph_ps (__mmask16 k, __m256h a, int sae);
</pre>
<pre>VCVTPH2PSX __m128 _mm_cvtxph_ps (__m128h a);
</pre>
<pre>VCVTPH2PSX __m128 _mm_mask_cvtxph_ps (__m128 src, __mmask8 k, __m128h a);
</pre>
<pre>VCVTPH2PSX __m128 _mm_maskz_cvtxph_ps (__mmask8 k, __m128h a);
</pre>
<pre>VCVTPH2PSX __m256 _mm256_cvtxph_ps (__m128h a);
</pre>
<pre>VCVTPH2PSX __m256 _mm256_mask_cvtxph_ps (__m256 src, __mmask8 k, __m128h a);
</pre>
<pre>VCVTPH2PSX __m256 _mm256_maskz_cvtxph_ps (__mmask8 k, __m128h a);
</pre>
<pre>VCVTPH2PSX __m512 _mm512_cvtxph_ps (__m256h a);
</pre>
<pre>VCVTPH2PSX __m512 _mm512_mask_cvtxph_ps (__m512 src, __mmask16 k, __m256h a);
</pre>
<pre>VCVTPH2PSX __m512 _mm512_maskz_cvtxph_ps (__mmask16 k, __m256h a);
</pre>
<h3 class="exceptions" id="simd-floating-point-exceptions">SIMD Floating-Point Exceptions<a class="anchor" href="#simd-floating-point-exceptions">
			¶
		</a></h3>
<p>VEX-encoded instructions: Invalid.</p>
<p>EVEX-encoded instructions: Invalid.</p>
<p>EVEX-encoded instructions with broadcast (VCVTPH2PSX): Invalid, Denormal.</p>
<h3 class="exceptions" id="other-exceptions">Other Exceptions<a class="anchor" href="#other-exceptions">
			¶
		</a></h3>
<p>VEX-encoded instructions, see <span class="not-imported">Table 2-26</span>, “Type 11 Class Exception Conditions” (do not report #AC).</p>
<p>EVEX-encoded instructions, see <span class="not-imported">Table 2-60</span>, “Type E11 Class Exception Conditions.”</p>
<p>EVEX-encoded instructions with broadcast (VCVTPH2PSX), see <span class="not-imported">Table 2-46</span>, “Type E2 Class Exception Conditions.”</p>
<p>Additionally:</p>
<table>
<tr>
<td>#UD</td>
<td>If VEX.W=1.</td></tr>
<tr>
<td>#UD</td>
<td>If VEX.vvvv != 1111B or EVEX.vvvv != 1111B.</td></tr></table><footer><p>
		This UNOFFICIAL, mechanically-separated, non-verified reference is provided for convenience, but it may be
		inc<span style="opacity: 0.2">omp</span>lete or b<sub>r</sub>oke<sub>n</sub> in various obvious or non-obvious
		ways. Refer to <a href="https://software.intel.com/en-us/download/intel-64-and-ia-32-architectures-sdm-combined-volumes-1-2a-2b-2c-2d-3a-3b-3c-3d-and-4">Intel® 64 and IA-32 Architectures Software Developer’s Manual</a> for anything serious.
	</p></footer></body></html>
</input>

<output>
<instruction mnemonic="VCVTPH2PS" brief="Convert packed FP16 values to packed single precision floating-point value"/>
<instruction mnemonic="VCVTPH2PSX" brief="Convert packed FP16 values to packed single precision floating-point value with broadcast"/>
<description>
This instruction converts packed half precision (16-bits) floating-point values in the low-order bits of the source operand (the second operand) to packed single precision floating-point values and writes the converted values into the destination operand (the first operand).

If case of a denormal operand, the correct normal result is returned. MXCSR.DAZ is ignored and is treated as if it 0. No denormal exception is reported on MXCSR.

VEX.128 version: The source operand is a XMM register or 64-bit memory location. The destination operand is a XMM register. The upper bits (MAXVL-1:128) of the corresponding destination register are zeroed.

VEX.256 version: The source operand is a XMM register or 128-bit memory location. The destination operand is a YMM register. Bits (MAXVL-1:256) of the corresponding destination register are zeroed.

EVEX encoded versions: The source operand is a YMM/XMM/XMM (low 64-bits) register or a 256/128/64-bit memory location. The destination operand is a ZMM/YMM/XMM register conditionally updated with writemask k1.

The VCVTPH2PSX instruction is a new form of the PH to PS conversion instruction, encoded in map 6. The previous version of the instruction, VCVTPH2PS, that is present in AVX512F (encoded in map 2, 0F38) does not support embedded broadcasting. The VCVTPH2PSX instruction has the embedded broadcasting option available.

The instructions associated with AVX512_FP16 always handle FP16 denormal number inputs; denormal inputs are not treated as zero.
</description>
</output>
</example>

<example>
<input>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:svg="http://www.w3.org/2000/svg" xmlns:x86="http://www.felixcloutier.com/x86"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><link rel="stylesheet" type="text/css" href="style.css"></link><title>FADD/FADDP/FIADD
		— Add</title></head><body><header><nav><ul><li><a href='/x86/'>Index</a></li><li>December 2023</li></ul></nav></header><h1>FADD/FADDP/FIADD
		— Add</h1>



<table>
<tr>
<th>Opcode</th>
<th>Instruction</th>
<th>64-Bit Mode</th>
<th>Compat/Leg Mode</th>
<th>Description</th></tr>
<tr>
<td>D8 /0</td>
<td>FADD m32fp</td>
<td>Valid</td>
<td>Valid</td>
<td>Add m32fp to ST(0) and store result in ST(0).</td></tr>
<tr>
<td>DC /0</td>
<td>FADD m64fp</td>
<td>Valid</td>
<td>Valid</td>
<td>Add m64fp to ST(0) and store result in ST(0).</td></tr>
<tr>
<td>D8 C0+i</td>
<td>FADD ST(0), ST(i)</td>
<td>Valid</td>
<td>Valid</td>
<td>Add ST(0) to ST(i) and store result in ST(0).</td></tr>
<tr>
<td>DC C0+i</td>
<td>FADD ST(i), ST(0)</td>
<td>Valid</td>
<td>Valid</td>
<td>Add ST(i) to ST(0) and store result in ST(i).</td></tr>
<tr>
<td>DE C0+i</td>
<td>FADDP ST(i), ST(0)</td>
<td>Valid</td>
<td>Valid</td>
<td>Add ST(0) to ST(i), store result in ST(i), and pop the register stack.</td></tr>
<tr>
<td>DE C1</td>
<td>FADDP</td>
<td>Valid</td>
<td>Valid</td>
<td>Add ST(0) to ST(1), store result in ST(1), and pop the register stack.</td></tr>
<tr>
<td>DA /0</td>
<td>FIADD m32int</td>
<td>Valid</td>
<td>Valid</td>
<td>Add m32int to ST(0) and store result in ST(0).</td></tr>
<tr>
<td>DE /0</td>
<td>FIADD m16int</td>
<td>Valid</td>
<td>Valid</td>
<td>Add m16int to ST(0) and store result in ST(0).</td></tr></table>
<h2 id="description">Description<a class="anchor" href="#description">
			¶
		</a></h2>
<p>Adds the destination and source operands and stores the sum in the destination location. The destination operand is always an FPU register; the source operand can be a register or a memory location. Source operands in memory can be in single precision or double precision floating-point format or in word or doubleword integer format.</p>
<p>The no-operand version of the instruction adds the contents of the ST(0) register to the ST(1) register. The one-operand version adds the contents of a memory location (either a floating-point or an integer value) to the contents of the ST(0) register. The two-operand version, adds the contents of the ST(0) register to the ST(i) register or vice versa. The value in ST(0) can be doubled by coding:</p>
<p>FADD ST(0), ST(0);</p>
<p>The FADDP instructions perform the additional operation of popping the FPU register stack after storing the result. To pop the register stack, the processor marks the ST(0) register as empty and increments the stack pointer (TOP) by 1. (The no-operand version of the floating-point add instructions always results in the register stack being popped. In some assemblers, the mnemonic for this instruction is FADD rather than FADDP.)</p>
<p>The FIADD instructions convert an integer source operand to double extended-precision floating-point format before performing the addition.</p>
<p>The table on the following page shows the results obtained when adding various classes of numbers, assuming that neither overflow nor underflow occurs.</p>
<p>When the sum of two operands with opposite signs is 0, the result is +0, except for the round toward −∞ mode, in which case the result is −0. When the source operand is an integer 0, it is treated as a +0.</p>
<p>When both operand are infinities of the same sign, the result is ∞ of the expected sign. If both operands are infinities of opposite signs, an invalid-operation exception is generated. See <a href='/x86/fadd:faddp:fiadd#tbl-3-18'>Table 3-18</a>.</p>
<figure id="tbl-3-18">
<table>
<tr>
<th colspan="9">DEST</th></tr>
<tr>
<td rowspan="8"><strong>SRC</strong></td>
<td></td>
<td>−∞</td>
<td>−F</td>
<td>−0</td>
<td>+0</td>
<td>+F</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>−∞</td>
<td>−∞</td>
<td>−∞</td>
<td>−∞</td>
<td>−∞</td>
<td>−∞</td>
<td>*</td>
<td>NaN</td></tr>
<tr>
<td>− F or − I</td>
<td>−∞</td>
<td>−F</td>
<td>SRC</td>
<td>SRC</td>
<td>± F or ± 0</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>−0</td>
<td>−∞</td>
<td>DEST</td>
<td>−0</td>
<td>±0</td>
<td>DEST</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>+0</td>
<td>−∞</td>
<td>DEST</td>
<td>±0</td>
<td>+0</td>
<td>DEST</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>+ F or + I</td>
<td>−∞</td>
<td>± F or ± 0</td>
<td>SRC</td>
<td>SRC</td>
<td>+F</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>+∞</td>
<td>*</td>
<td>+∞</td>
<td>+∞</td>
<td>+∞</td>
<td>+∞</td>
<td>+∞</td>
<td>NaN</td></tr>
<tr>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td>
<td>NaN</td></tr></table>
<figcaption><a href='/x86/fadd:faddp:fiadd#tbl-3-18'>Table 3-18</a>. FADD/FADDP/FIADD Results</figcaption></figure>
<blockquote>
<p>F Means finite floating-point value.</p>
<p>I Means integer.</p>
<p>* Indicatesfloating-pointinvalid-arithmetic-operand(#IA)exception.</p></blockquote>
<p>This instruction’s operation is the same in non-64-bit modes and 64-bit mode.</p>
<h2 id="operation">Operation<a class="anchor" href="#operation">
			¶
		</a></h2>
<pre>IF Instruction = FIADD
    THEN
        DEST := DEST + ConvertToDoubleExtendedPrecisionFP(SRC);
    ELSE (* Source operand is floating-point value *)
        DEST := DEST + SRC;
FI;
IF Instruction = FADDP
    THEN
        PopRegisterStack;
FI;
</pre>
<h2 id="fpu-flags-affected">FPU Flags Affected<a class="anchor" href="#fpu-flags-affected">
			¶
		</a></h2>
<table>
<tr>
<td rowspan="2">C1</td>
<td>Set to 0 if stack underflow occurred.</td></tr>
<tr>
<td>Set if result was rounded up; cleared otherwise.</td></tr>
<tr>
<td>C0, C2, C3</td>
<td>Undefined.</td></tr></table>
<h2 class="exceptions" id="floating-point-exceptions">Floating-Point Exceptions<a class="anchor" href="#floating-point-exceptions">
			¶
		</a></h2>
<table>
<tr>
<td>#IS</td>
<td>Stack underflow occurred.</td></tr>
<tr>
<td rowspan="2">#IA</td>
<td>Operand is an SNaN value or unsupported format.</td></tr>
<tr>
<td>Operands are infinities of unlike sign.</td></tr>
<tr>
<td>#D</td>
<td>Source operand is a denormal value.</td></tr>
<tr>
<td>#U</td>
<td>Result is too small for destination format.</td></tr>
<tr>
<td>#O</td>
<td>Result is too large for destination format.</td></tr>
<tr>
<td>#P</td>
<td>Value cannot be represented exactly in destination format.</td></tr></table>
<h2 class="exceptions" id="protected-mode-exceptions">Protected Mode Exceptions<a class="anchor" href="#protected-mode-exceptions">
			¶
		</a></h2>
<table>
<tr>
<td rowspan="2">#GP(0)</td>
<td>If a memory operand effective address is outside the CS, DS, ES, FS, or GS segment limit.</td></tr>
<tr>
<td>If the DS, ES, FS, or GS register contains a NULL segment selector.</td></tr>
<tr>
<td>#SS(0)</td>
<td>If a memory operand effective address is outside the SS segment limit.</td></tr>
<tr>
<td>#NM</td>
<td>CR0.EM[bit 2] or CR0.TS[bit 3] = 1.</td></tr>
<tr>
<td>#PF(fault-code)</td>
<td>If a page fault occurs.</td></tr>
<tr>
<td>#AC(0)</td>
<td>If alignment checking is enabled and an unaligned memory reference is made while the current privilege level is 3.</td></tr>
<tr>
<td>#UD</td>
<td>If the LOCK prefix is used.</td></tr></table>
<h2 class="exceptions" id="real-address-mode-exceptions">Real-Address Mode Exceptions<a class="anchor" href="#real-address-mode-exceptions">
			¶
		</a></h2>
<table>
<tr>
<td>#GP</td>
<td>If a memory operand effective address is outside the CS, DS, ES, FS, or GS segment limit.</td></tr>
<tr>
<td>#SS</td>
<td>If a memory operand effective address is outside the SS segment limit.</td></tr>
<tr>
<td>#NM</td>
<td>CR0.EM[bit 2] or CR0.TS[bit 3] = 1.</td></tr>
<tr>
<td>#UD</td>
<td>If the LOCK prefix is used.</td></tr></table>
<h2 class="exceptions" id="virtual-8086-mode-exceptions">Virtual-8086 Mode Exceptions<a class="anchor" href="#virtual-8086-mode-exceptions">
			¶
		</a></h2>
<table>
<tr>
<td>#GP(0)</td>
<td>If a memory operand effective address is outside the CS, DS, ES, FS, or GS segment limit.</td></tr>
<tr>
<td>#SS(0)</td>
<td>If a memory operand effective address is outside the SS segment limit.</td></tr>
<tr>
<td>#NM</td>
<td>CR0.EM[bit 2] or CR0.TS[bit 3] = 1.</td></tr>
<tr>
<td>#PF(fault-code)</td>
<td>If a page fault occurs.</td></tr>
<tr>
<td>#AC(0)</td>
<td>If alignment checking is enabled and an unaligned memory reference is made.</td></tr>
<tr>
<td>#UD</td>
<td>If the LOCK prefix is used.</td></tr></table>
<h2 class="exceptions" id="compatibility-mode-exceptions">Compatibility Mode Exceptions<a class="anchor" href="#compatibility-mode-exceptions">
			¶
		</a></h2>
<p>Same exceptions as in protected mode.</p>
<h2 class="exceptions" id="64-bit-mode-exceptions">64-Bit Mode Exceptions<a class="anchor" href="#64-bit-mode-exceptions">
			¶
		</a></h2>
<table>
<tr>
<td>#SS(0)</td>
<td>If a memory address referencing the SS segment is in a non-canonical form.</td></tr>
<tr>
<td>#GP(0)</td>
<td>If the memory address is in a non-canonical form.</td></tr>
<tr>
<td>#NM</td>
<td>CR0.EM[bit 2] or CR0.TS[bit 3] = 1.</td></tr>
<tr>
<td>#MF</td>
<td>If there is a pending x87 FPU exception.</td></tr>
<tr>
<td>#PF(fault-code)</td>
<td>If a page fault occurs.</td></tr>
<tr>
<td>#AC(0)</td>
<td>If alignment checking is enabled and an unaligned memory reference is made while the current privilege level is 3.</td></tr>
<tr>
<td>#UD</td>
<td>If the LOCK prefix is used.</td></tr></table><footer><p>
		This UNOFFICIAL, mechanically-separated, non-verified reference is provided for convenience, but it may be
		inc<span style="opacity: 0.2">omp</span>lete or b<sub>r</sub>oke<sub>n</sub> in various obvious or non-obvious
		ways. Refer to <a href="https://software.intel.com/en-us/download/intel-64-and-ia-32-architectures-sdm-combined-volumes-1-2a-2b-2c-2d-3a-3b-3c-3d-and-4">Intel® 64 and IA-32 Architectures Software Developer’s Manual</a> for anything serious.
	</p></footer></body></html>
</input>

<output>
<instruction mnemonic="FADD" brief="Adds the destination and source operands and stores the sum in the destination location"/>
<instruction mnemonic="FADDP" brief="Adds the destination and source operands, and pop the register stack"/>
<instruction mnemonic="FIADD" brief="Adds the destination and source operands, and convert the source operand to double extended-precision floating-point format before performing the addition"/>
<description>
Adds the destination and source operands and stores the sum in the destination location. The destination operand is always an FPU register; the source operand can be a register or a memory location. Source operands in memory can be in single precision or double precision floating-point format or in word or doubleword integer format.

The no-operand version of the instruction adds the contents of the ST(0) register to the ST(1) register. The one-operand version adds the contents of a memory location (either a floating-point or an integer value) to the contents of the ST(0) register. The two-operand version, adds the contents of the ST(0) register to the ST(i) register or vice versa. The value in ST(0) can be doubled by coding:

FADD ST(0), ST(0);

The FADDP instructions perform the additional operation of popping the FPU register stack after storing the result. To pop the register stack, the processor marks the ST(0) register as empty and increments the stack pointer (TOP) by 1. (The no-operand version of the floating-point add instructions always results in the register stack being popped. In some assemblers, the mnemonic for this instruction is FADD rather than FADDP.)

The FIADD instructions convert an integer source operand to double extended-precision floating-point format before performing the addition.

The table on the following page shows the results obtained when adding various classes of numbers, assuming that neither overflow nor underflow occurs.

When the sum of two operands with opposite signs is 0, the result is +0, except for the round toward −∞ mode, in which case the result is −0. When the source operand is an integer 0, it is treated as a +0.

When both operand are infinities of the same sign, the result is ∞ of the expected sign. If both operands are infinities of opposite signs, an invalid-operation exception is generated.
</description>
</output>
</example>
"""


def fetch_page(url):
    """Fetch a page with retry logic and rate limiting."""
    # Cache to `/tmp/x86/url_hash.html`
    key = hashlib.md5(url.encode()).hexdigest() 
    cache_file = os.path.join('/tmp/x86', key + '.html')
    if os.path.exists(cache_file):
        return open(cache_file, 'r').read(), key
    
    for _ in range(3):  # retry up to 3 times
        try:
            response = requests.get(url)
            response.raise_for_status()
            time.sleep(0.5)  # Be nice to the server
            with open(cache_file, 'w') as f:
                f.write(response.text)
            return response.text, key
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(1)  # Wait before retry
    return None, None

def batch_submit_instructions():
    """Fetch and parse all instructions from the main page."""
    html, _ = fetch_page(BASE_URL)
    if not html:
        return []
    
    client = anthropic.Anthropic()
    soup = BeautifulSoup(html, 'html.parser')
    url_data = {}
    batch_requests = []
    
    # Find all instruction links in the tables
    for table in soup.find_all('table'):
        for link in tqdm(table.find_all('a'), desc="Processing links"):
            href = link.get('href')
            if not href or not href.startswith('/') or href == 'index.html':
                continue
            
            full_url= urljoin(BASE_URL, href)
            if full_url in url_data:
                continue
            
            html, key = fetch_page(full_url)
            if html is None:
                continue

            url_data[full_url] = html
            batch_requests.append(Request(
                custom_id=key,
                params=MessageCreateParamsNonStreaming(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=4096,
                        temperature=0.8,
                        system=[{
                            "type": "text",
                            "text": BASE_PROMT,
                            "cache_control": {"type": "ephemeral"}
                        }],
                        messages=[{
                            "role": "user",
                            "content": "<input>\n" + html + "\n</input>"
                        },
                        {
                            "role": "assistant",
                            "content": "<output>\n<instruction mnemonic"
                        }
                        ],
                        stop_sequences=["</output>"]
                    )
            ))

    message_batch = client.messages.batches.create(requests=batch_requests)
    print(message_batch)

def main():
    batch_submit_instructions()

if __name__ == '__main__':
    main()


