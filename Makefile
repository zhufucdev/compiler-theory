LEX = flex
YACC = bison
CC = gcc
NASM = nasm
PY = python3
file = test1
ALL: $(file)
machine := $(shell uname -m)
lex.yy.c: lex.l
	$(LEX) -o out/lex.yy.c lex.l

yacc.tab.c yacc.tab.h: yacc.y hashMap.h tree.h
	mkdir -p out
	$(YACC) -d yacc.y -o out/yacc.tab.c

Compiler: yacc.tab.c yacc.tab.h lex.yy.c hashMap.h tree.h tree.c
	$(CC) -o out/compiler out/yacc.tab.c out/lex.yy.c tree.c stack.c hashMap.c inner.c -lfl

Innercode: Compiler
	cp samples/$(file).c out/test.c
	cd out && ./compiler test.c

assembly.s: assembly.py Innercode
	cd out && python3 ../assembly.py

ifeq ($(machine), x86_64)
test.o: assembly.s
	cd out && nasm -f elf64 $< -o $@
else
test.o: assembly.s
	cd out && as $< -o $@
endif

$(file): test.o
	cd out && $(CC) -no-pie -e _start -o $@ $<

clean:
	rm -rf out/*
