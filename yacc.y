%{
    #include "../tree.h"
    #include "../hashMap.h"
    #include "../inner.h"
    #include <stdio.h>
    #include <string.h>
    void output();
    int yylex();
    void yyerror(const char *s);
    extern int yylineno;
    extern FILE* yyout;
    FILE *out,*outInner;

    HashMap* hashMap = NULL;
    Array *globalArray = NULL;
    Array *lastGlobalArray = NULL;

    int scope = 0;
    struct Declator* declator;
    int type;
    int preType;

    Tree* root;
    Node *head;
    int line_count=1;
%}
%union{
    struct Tree* tree;
}
%token <tree> INT8 INT10 INT16
%token <tree> ID
%token <tree> INT
%token <tree> VOID MAIN RET CONST STATIC AUTO IF ELSE WHILE DO BREAK CONTINUE SWITCH CASE
%token <tree> DEFAULT SIZEOF TYPEDEF VOLATILE GOTO INPUT OUTPUT
%token <tree> LE GE AND OR ADD_ASSIGN SUB_ASSIGN MUL_ASSIGN DIV_ASSIGN MOD_ASSIGN
%token <tree> INC DEC EQUAL NE PTR FOR STR
%token <tree> '(' ')' '[' ']' '{' '}' '!' '^' '&' '*' '-' '+' '=' '/' '%' ',' ';' '<' '>'
%type <tree> type
%type <tree> constant primary_expression postfix_expression unary_expression cast_expression
multiplicative_expression additive_expression relational_expression equality_expression
logical_and_expression logical_or_expression assignment_expression operate_expression declare_expression
nullable_expression while_expression for_expression funcion_expression if_expression if_identifier return_expression null unary_operator
main_function sentence statement assignment_operator single_expression

%precedence ')'
%precedence ELSE

%%


project:
    main_function
    {
        root = createTree("Project", 1, $1);

        //重新赋值行号
        int seek=1;
        line_count=1;
        if(root->code){
            while(seek){
                seek = swap(root->code,"#",lineToString(line_count++));
            }
            fprintf(outInner, "%s\n%s", getAllocations(globalArray), root->code);
        }
    }
;

main_function
    : VOID MAIN '(' ')' '{' sentence '}'
    {
        $$ = createTree("Main Func", 7, $1, $2, $3, $4, $5, $6, $7);
    }
    | type MAIN '(' ')' '{' sentence '}'
    {
        $$ = createTree("Main Func", 7, $1, $2, $3, $4, $5, $6, $7);
    }
;

sentence
    : statement sentence
    {
        $$ = createTree("sentence", 2, $1, $2);
    }
    | statement

;
constant
    : INT8
    | INT10
    | INT16
;

primary_expression
    : ID
    {
        if(type == 0){
            Data* data = toData(type, $1->content, NULL, scope);
            HashNode* hashNode = get(hashMap, data);
            if(hashNode == NULL){
                char* error = (char*)malloc(50);
                sprintf(error, "\"%s\" is undefined", $1->content);
                yyerror(error);
                free(error);
            }
        }
    }
    | constant
    | '(' operate_expression ')'
    {
        $$ = createTree("primary_expression", 3, $1, $2, $3);
    }
;

postfix_expression
    : primary_expression
    | postfix_expression '[' operate_expression ']'
    {
        $$ = addDeclator("Array", $1, $3);
    }
    | postfix_expression INC
    {
        $$ = createTree("postfix_expression", 2, $1, $2);
    }
    | postfix_expression DEC
    {
        $$ = createTree("postfix_expression", 2, $1, $2);
    }
;

unary_operator
    : '+'
    | '-'
    | '*' {  type = preType; }
    | '&'
    | '!'
;

unary_expression
    : postfix_expression
    | INC postfix_expression
    {
        $$ = unaryOpr("unary_expression", $1, $2);
    }
    | DEC postfix_expression
    {
        $$ = unaryOpr("unary_expression", $1, $2);
    }
    | unary_operator cast_expression
    {
        if(!strcmp($1->content, "*")){
            $$ = addDeclator("Pointer", $2, $1);
        }else{
            $$ = unaryOpr("unary_expression", $1, $2);
        }
    }
;

cast_expression
    : unary_expression

;

multiplicative_expression
    : cast_expression
    | multiplicative_expression '*' cast_expression
    {
        $$ = binaryOpr("multiplicative_expression", $1, $2, $3);
    }
    | multiplicative_expression '/' cast_expression
    {
        $$ = binaryOpr("multiplicative_expression", $1, $2, $3);
    }
    | multiplicative_expression '%' cast_expression
    {
        $$ = binaryOpr("multiplicative_expression", $1, $2, $3);
    }
    | multiplicative_expression '^' cast_expression
    {
        $$ = binaryOpr("multiplicative_expression", $1, $2, $3);
    }
;

additive_expression
    : multiplicative_expression

    | additive_expression '+' multiplicative_expression
    {
        $$ = binaryOpr("additive_expression", $1, $2, $3);
    }
    | additive_expression '-' multiplicative_expression
    {
        $$ = binaryOpr("additive_expression", $1, $2, $3);
    }
;

relational_expression
    : additive_expression
    | relational_expression '<' additive_expression
    {
        $$ = binaryOpr("relational_expression", $1, $2, $3);
    }
    | relational_expression '>' additive_expression
    {
        $$ = binaryOpr("relational_expression", $1, $2, $3);
    }
    | relational_expression LE additive_expression
    {
        $$ = binaryOpr("relational_expression", $1, $2, $3);
    }
    | relational_expression GE additive_expression
    {
        $$ = binaryOpr("relational_expression", $1, $2, $3);
    }
;

equality_expression
    : relational_expression
    | equality_expression EQUAL relational_expression
    {
        $$ = binaryOpr("equality_expression", $1, $2, $3);
    }
    | equality_expression NE relational_expression
    {
        $$ = binaryOpr("equality_expression", $1, $2, $3);
    }
;

logical_and_expression
    : equality_expression
    | logical_and_expression AND equality_expression
    {
        $$ = binaryOpr("logical_and_expression", $1, $2, $3);
    }
;

logical_or_expression
    : logical_and_expression
    | logical_or_expression OR logical_and_expression
    {
        $$ = binaryOpr("logical_or_expression", $1, $2, $3);
    }
;

assignment_operator
    : '='
    | MUL_ASSIGN
    | DIV_ASSIGN
    | MOD_ASSIGN
    | ADD_ASSIGN
    | SUB_ASSIGN
;

assignment_expression
    : logical_or_expression
    | unary_expression assignment_operator assignment_expression
    {
        $$ = assignOpr("assignment_expression", $1, $2, $3);
    }
;

operate_expression
    : assignment_expression
    | operate_expression ',' assignment_expression
    {
        $$ = createTree("operate_expression", 3, $1, $2, $3);
    }
;

null:{$$ = createTree("null", 0, yylineno);};

nullable_expression
    : null
    | operate_expression
;

declare_expression
    : type operate_expression
    {
        $$ = createTree("declare_expression", 2, $1, $2);
        if($2){
            putTree(hashMap, $2);
            preType = type = 0;


            lastGlobalArray = addArray(lastGlobalArray, $2);
        }
    }
;

single_expression
    : operate_expression ';'
    | declare_expression ';'
    | if_expression
    | while_expression
    | for_expression
    | funcion_expression ';'
    | return_expression ';'
    | ';'
;

if_expression
    : if_identifier ')' statement
    {
        int headline = $1->headline;
        int nextline = line_count;
        $$ = ifOpr("if_expression",headline,nextline, $1, $3);
    }
    | if_identifier ')' statement ELSE {$1->nextline = line_count++;} statement
    {
        int headline = $1->headline;
        int next1 = $1->nextline;
        int next2 = line_count;
        $$ = ifelseOpr("if_else_expression",headline,next1,next2, $1, $3, $6);
    }
;
if_identifier
    : IF  '(' operate_expression
    {
        $$ = $3;
        $$->headline = line_count;
        line_count += 2;
    }
;


statement
    : '{' sentence '}'
    {
        $$ = createTree("statement", 3, $1, $2, $3);
    }
    | '{' '}'
    {
        $$ = createTree("statement", 2, $1, $2);
    }
    | single_expression  {head = NULL;}
;

for_expression
    : FOR '(' nullable_expression {
        $1->headline = line_count;
    } ';'  nullable_expression ';' {
        $6->headline = line_count;
    } nullable_expression ')' {

    } statement
    {
        line_count += 2;
        int head1 = $1->headline;
        int head2 = $6->headline;
        int nextline = line_count++;
        $$ = forOpr("for_expression",head1, head2, nextline, $3, $6, $9, $12);
    }
;

while_expression
    : WHILE {
        $1->headline = line_count;
    }'(' operate_expression ')' {
        $4->headline = line_count;
        line_count += 2;
    } statement{
        int head1 = $1->headline;
        int head2 = $4->headline;
        int nextline = line_count++;
        $$ = whileOpr("while_expression",head1, head2, nextline, $4, $7);
    }
;

funcion_expression
    : INPUT '(' operate_expression ')'
    {
        $$ = unaryFunc("input", $1, $3);
        line_count+=2;
    }
    | OUTPUT '(' operate_expression ')'
    {
        $$ = unaryFunc("output", $1, $3);
        line_count+=2;
    }
;

return_expression
    : RET
    {
        $$ = retNull("return_expression", $1);
    }
    | RET operate_expression
    {
        $$ = retOpr("return_expression", $1, $2);
    }
;

type
    : INT {
        // $$ = createTree("type", 1, $1);
        type = INT;
    }
%%




void yyerror(const char* s){
    printf("Error: %s\tline: %d\n", s, yylineno);
}

int main(int argc, char* argv[]){
    const char* outFile="lexical";
    const char* outFile2="grammatical";
    const char* outFile3="innercode";
    extern FILE* yyin, *yyout;
    type = 0;
    hashMap = createHashMap(2);
    globalArray = emptyArray();
    lastGlobalArray = globalArray;
	yyin = fopen(argv[1], "r");
    yyout = fopen(outFile, "w");
    out = fopen(outFile2,"w");
    outInner = fopen(outFile3,"w");
    int i = 0;
    fprintf(yyout, "%-15s\t%-15s\t%s\n", "Token", "Literal", "Properties");
	if(!yyparse()){
        printf("read successfully\n");
        printTree(root);
    }
	else{
        printf("something error\n");
    }
    fclose(out);
    fclose(outInner);
	fclose(yyin);
    fclose(yyout);
    destoryHashMap(hashMap);
	return 0;
}
