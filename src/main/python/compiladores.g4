grammar compiladores;

fragment LETRA : [A-Za-z] ;
fragment DIGITO : [0-9] ;

PA : '('; //esto puede ser una expresion especifica
PC : ')'; //esto puede ser una expresion especifica
PYC : ';';
LLA : '{';
LLC : '}';
COMA: ',';
PUNTO: '.';

ASIG : '=';
IGUAL : '==';
SUMA: '+' ;
RESTA: '-' ;
MULT: '*' ;
DIV: '/' ;
MOD: '%' ;
MAY: '>' ;
MEN: '<' ;
MAYI: '>=' ;
MENI: '<=' ;
OR: '||' ;
AND: '&&' ;

TRUE: 'TRUE';
FALSE: 'FALSE';

NUMERO : DIGITO+ ;

INT: 'int';
BOOL: 'bool';
FLOAT: 'float';
DOUBLE: 'double';
VOID: 'void';

WHILE: 'while';
FOR: 'for';
IF: 'if';
ELSE: 'else';
RETURN: 'return';

BOOLEANS: TRUE
        | FALSE
        ;

ID: (LETRA | '_')(LETRA | DIGITO | '_')*; //expresion regular

WS: [ \t\n\r] -> skip;
OTRO : . ;//por si no entra en ninguna regla; si no esta esto lo toma como un error lexico

// analisis sintactico:
si : s EOF; //veo desde la raiz; simbolo inicial

s : PA s PC s
  |
  ;

programa: instrucciones EOF;

instrucciones : instruccion instrucciones
              |
              ;
instruccion : declaracionPYC
            | iwhile
            | ifor
            | iif
            | asignacionPYC
            | protofun
            | inic
            | returnfun PYC
            | bloqueSolo //porque puede ser un bloque solo
            | deffuncion
            | llamadafun
            ;
bloqueSolo : LLA instrucciones LLC;
inic: tipoDatos asignacionNum PYC
    | tipoDatos asignacionBool PYC;
declaracion : tipoDatos ID;
tipoDatos: BOOL
          | INT
          | FLOAT
          | DOUBLE
          ; 
declaracionPYC: declaracion PYC;
asignacionNum : ID ASIG exp;

asignacionPYC: asignacion PYC;

asignacion : asignacionNum
            | asignacionBool
            ;


ifor : FOR PA init PYC cond PYC iter PC bloque;
init : asignacionNum;

exp: term expPrima;

expPrima: SUMA exp
        | RESTA exp
        | //Esto es una regla vacia, para cuando no hay mas terminos para operar
        ;

term: factor t ;
t    : MULT factor t
    | DIV factor t
    | MOD factor t
    |
    ;
factor: NUMERO
      | ID
      | funcionVar
      | PA exp PC
      ;
funcionVar: ID PA ids PC;
ids: (ID | NUMERO | BOOLEANS ) iden
   |
   ;
iden : COMA ids
      |
      ;

iwhile : WHILE PA cond PC bloque;

bloque : LLA instrucciones LLC
       | instruccion
       ;

comps: MEN
      | MAY
      | MENI
      | MAYI
      | IGUAL
      ;
bools: OR opbool
      | AND opbool
      |
      ;
factorBool: TRUE
          | FALSE
          ;
asignacionBool : ID ASIG opbool;
opbool : factorBool bools ;
opcomp : ID comps factor;

cond : opcomp cond// si quiero que la condicion tenga una operacion algebraica DEBE ESTAR ENTRE PARENTESIS
      | opbool cond
      |
      ;
iter: ID ASIG ID iteracion; //i = i+1;
iteracion: SUMA NUMERO
          | RESTA NUMERO
          | MULT NUMERO
          | DIV NUMERO
          ;
iif: IF PA cond PC bloque
   | IF PA cond PC bloque else;
else: ELSE bloque
    | ELSE iif
    ;

funcion: ID PA argumentos PC;
return: tipoDatos
      | VOID
      ;
returnfun: RETURN exp
         | RETURN VOID
         ;
protofun: return funcion PYC;
deffuncion: return funcion LLA instrucciones LLC;
llamadafun: funcionVar;
argumentos: argumento arg
          |
          ;
arg : COMA argumentos
    |
    ;
argumento: tipoDatos ID;