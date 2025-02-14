Sublimeassembly 2
=================
New version of Sublime Text NASM syntax that you love, now with built-in documentation and auto-completion for most instructions. 
Documentation and auto-completions only work in Sublime Text 3 and above

More features are coming but contribution is always welcome.

Also available on Package Control as NASM x86 Assembly 

# Contributing
Syntax is now auto generated from `instructions.json` which serves as the source of truth.
This file contains the mnemonics, their alises and descriptions.

The syntax can be regenerated like
```bash
$ ./etc/generate_syntax.py
```

This file is mechanically generated from [Felix's Reference](https://www.felixcloutier.com/x86/).
Since Felix in turn mechnically generates his data from PDFs the resulting data format is not very
stable. So...we just feed the HTML into an LLM and pray. 

The generated data is reasonable so we'll stick with it.


# LICENSE
Copyright (c) 2015, Pavlo Malynin
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Pavlo Malynin nor the
      names of the contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


