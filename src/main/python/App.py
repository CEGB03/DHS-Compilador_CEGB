import sys
from antlr4 import *
from compiladoresLexer  import compiladoresLexer
from compiladoresParser import compiladoresParser
from Escucha import Escucha
from Walker import Walker

def main(argv):
    archivo = "input/opal.txt"
    if len(argv) > 1 :
        archivo = argv[1]
    input = FileStream(archivo)
    lexer = compiladoresLexer(input) #cuando encuentra algo parecido a una regla, devuelve un token
    stream = CommonTokenStream(lexer) #acumula esos tokens
    parser = compiladoresParser(stream) #pide mas tokens, hasta que termine o encuentre un error
    escucha = Escucha()
    parser.addParseListener(escucha)
    tree = parser.programa() #con el arbol vamos a crear el codigo intermedio
    #print(tree.toStringTree(recog=parser))
    #caminante = Walker()
    #caminante.visitPrograma(tree)
    

if __name__ == '__main__':
    main(sys.argv)