# Dalia programming language. 
### Open to contrib

>[!NOTE]
> Bootstrap compiler (including infra) all in-house hopefully. Work is slow **THIS IS A LEARNING PROJECT!**. I am interested in pursuing language 
> development more and want to learn a little about making my own full compiler instead of relying on LLVM. This is a huge task and will for sure take time > :) so contribution to development is welcome!


### New(ish?) ideas?
- `m'` and `t'` are "prime forms". open issue for naming ideas or concerns! More on these later:tm:


as -o boot.o boot.s && ld -macosx_version_min 13.0.0 -o boot boot.o -lSystem -syslibroot `xcrun -sdk macosx --show-sdk-path` -e _start -arch arm64