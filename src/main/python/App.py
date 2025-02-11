import sys
import logging
import os
from antlr4 import *
from compiladoresLexer import compiladoresLexer
from compiladoresParser import compiladoresParser
from Escucha import Escucha
from Walker import Walker

# Crear el directorio output si no existe
os.makedirs('./output', exist_ok=True)

# Configurar el logger
logging.basicConfig(filename='./output/Errores&Warnings.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Redirigir la salida estándar de errores a un archivo
sys.stderr = open('./output/Errores&Warnings.txt', 'a')

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
    # print(tree.toStringTree(recog=parser))
    # si hay algun error, debera detenerse la ejecucion y no se construira el codigo intermedio
    if not escucha.error:
        caminante = Walker()
        try:
            caminante.visit(tree)
        except Exception as e:
            logging.error(f'Error en Walker: {e}')
            print('Ha ocurrido un error en Walker, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')
    else:
        logging.error('Ha ocurrido un error, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')

if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception as e:
        logging.error(f'Error inesperado: {e}')
        print('Ha ocurrido un error, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')