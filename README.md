# Trabajo Final - Desarrollo de Herramientas de Software

## Descripción

Este proyecto es un compilador desarrollado en Python utilizando ANTLR.  
Toma como entrada un archivo de código fuente en C (simplificado), realiza verificación gramatical y semántica, genera una tabla de símbolos, reporta errores y advertencias, y produce código intermedio en tres direcciones.

## Estructura del Proyecto

```
.
├── input/
│   ├── opal.txt
│   └── prueba.txt
├── output/
│   ├── CodigoIntermedio.txt
│   ├── Compilacion.txt
│   └── Errores&Warnings.txt
├── src/
│   └── main/
│       └── python/
│           ├── App.py
│           ├── Escucha.py
│           ├── Walker.py
│           ├── Squeleton.py
│           ├── compiladores.g4
│           ├── compiladoresLexer.py
│           ├── compiladoresParser.py
│           ├── compiladoresListener.py
│           └── compiladoresVisitor.py
├── Notas de Codigo Intermedio.txt
├── Consignas para el FInal.txt
├── Notas de Tabla de Simbolos.txt
└── README.md
```

## Cómo ejecutar

1. Instala las dependencias necesarias (ANTLR4, Python 3).
2. Genera los archivos de ANTLR si modificas la gramática:
   ```sh
   antlr4 -Dlanguage=Python3 compiladores.g4
   ```
3. Ejecuta el compilador:
   ```sh
   python3 src/main/python/App.py
   ```
4. Revisa los archivos de salida en la carpeta `output/`.

## Archivos de salida

- `output/Compilacion.txt`: Tabla de símbolos y reporte de compilación.
- `output/CodigoIntermedio.txt`: Código intermedio en tres direcciones.
- `output/Errores&Warnings.txt`: Errores y advertencias detectados.

## Notas

- Si hay errores, no se genera código intermedio.
- El proyecto sigue las consignas del trabajo final de la materia DHS.