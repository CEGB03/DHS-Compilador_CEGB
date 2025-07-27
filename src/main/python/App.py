import sys
import logging
import os
import glob
from antlr4 import *
from compiladoresLexer import compiladoresLexer
from compiladoresParser import compiladoresParser
from Escucha import Escucha
from Walker import Walker
from Optimizador import Optimizador
import traceback


# Crear el directorio output si no existe
os.makedirs('./output', exist_ok=True)

# Borrar todos los archivos de la carpeta output y recrearlos vacíos
for archivo in glob.glob('./output/*'):
    with open(archivo, 'w', encoding='utf-8') as f:
        pass

# Configurar el logger
logging.basicConfig(filename='./output/Errores&Warnings.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Redirigir la salida estándar de errores a un archivo
sys.stderr = open('./output/Errores&Warnings.txt', 'a')

def main(argv):
    archivo = "input/opal.txt"
    if len(argv) > 1:
        archivo = argv[1]
    else:
        print("¿Desea ejecutar el archivo por defecto (input/opal.txt)? [S/n]")
        respuesta = input().strip().lower()
        if respuesta == "n":
            archivo = input("Ingrese el path del archivo a ejecutar: ").strip()
            if not archivo:
                print("No se ingresó archivo, se usará el archivo por defecto.")
                archivo = "input/opal.txt"
        else:
            archivo = "input/opal.txt"  # <-- Agrega esto para el caso "s" o Enter
    input_stream = FileStream(archivo, encoding='utf-8')
    lexer = compiladoresLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = compiladoresParser(stream)
    escucha = Escucha()
    parser.addParseListener(escucha)
    tree = parser.programa() #con el arbol vamos a crear el codigo intermedio
    #print(tree.toStringTree(recog=parser)) # Permite ver como se desarrolla la gramatica
    # si hay algun error, debera detenerse la ejecucion y no se construira el codigo intermedio
    if not escucha.error:
        caminante = Walker()
        try:
            caminante.visit(tree)
            opt = Optimizador()
            opt.optimizar()
            

        except Exception as e:
            logging.error(f'Error en Walker: {e}')
            traceback.print_exc()  # <-- agrega esto para ver el stacktrace en consola
            print('Ha ocurrido un error en Walker, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')
    else:
        logging.error('Ha ocurrido un error, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')

if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception as e:
        logging.error(f'Error inesperado: {e}')
        print('Ha ocurrido un error, revisar el archivo ./output/Errores&Warnings.txt. No se genero codigo intermedio')