import os
import logging

from Squeleton import TablaSimbolos, Variable

class Optimizador:
    def __init__(self):
        self.ventanas = []
        self.tabla = TablaSimbolos.get_instancia()
        
    def optimizar(self):
        auxfile = "output/auxfile.txt"
        inroute = "output/CodigoIntermedio.txt"
        outroute = "output/codigoIntermedioOptimizado.txt"
        # Asegurar que el directorio de salida existe
        os.makedirs(os.path.dirname(auxfile), exist_ok=True)
        # Crear el archivo auxfile.txt si no existe
        open(auxfile, 'a').close()
        
        self.eliminar_acciones_repetidas(inroute, auxfile)
        self.propagacion_de_constantes(auxfile, outroute)
        self.eliminar_lineas_vacias(outroute)
        self.eliminar_lineas_vacias(auxfile)
        # Eliminar el archivo auxfile.txt al finalizar
        #os.remove(auxfile)
        
    def findventanas_oportunidad(self, infile):
        self.ventanas.clear()
        cod = infile.readlines()
        infile.seek(0)
        saltar = 0
        for i, line in enumerate(cod):
            current = line.split()
            if len(current) > 0:
                if saltar > 0:
                    saltar -= 1
                else:
                    if i > 0:
                        if i == len(cod) - 1:
                            self.close_ventana(i+1)
                        if current[0] == "push":
                            if self.is_llamado_a_funcion(i, cod):
                                saltar = 3
                                continue
                        if current[0] == "jmp":
                            self.enter_ventana(i+1)
                            continue
                        if current[0] == "label" or current[0] == "ifnjmp":
                            self.enter_ventana(i+1)
                            continue
                    else:
                        self.enter_ventana(i+1)
        if len(self.ventanas) == 0:
            self.ventanas.append([1,1])
        elif len(self.ventanas[-1]) == 1:
            self.close_ventana(i+1)
    
    def is_llamado_a_funcion(self, i, cod):
        if i + 3 < len(cod):
            current = cod[i].split()
            next = cod[i + 1].split()
            nnext = cod[i + 2].split()
            if next[0] == "jmp":
                if nnext and nnext[0] == "label" and nnext[1] == current[1]:
                    return True
        return False
    
    def close_ventana(self, lnum):
        self.ventanas[-1].append(lnum)
    
    def enter_ventana(self, lnum):
        if len(self.ventanas) > 0:
            self.ventanas[-1].append(lnum)
            if self.ventanas[-1][0] == self.ventanas[-1][1]:
                self.ventanas.pop()
            self.ventanas.append([lnum + 1])
        else:
            self.ventanas.append([lnum])
    
    def control_propagacion(self, currentline, valores):
        for start, end in self.ventanas:
            if currentline < end:
                return
            if currentline == end:
                valores.clear()
                self.ventanas.pop(0)
                return
    
    def control_eliminacion(self, currentline, acciones, sustitutos):
        for start, end in self.ventanas:
            if currentline < end:
                return
            if currentline == end:
                acciones.clear()
                sustitutos.clear()
                self.ventanas.pop(0)
                return
    
    def is_numeric_value(self, val: str):
        val = val.replace('.', '', 1)
        return val.isdigit()
    
    def limpiar_diccionario(self, diccionario, valor):
        diccionario_copy = diccionario.copy()
        for accion in diccionario_copy:
            if valor in accion:
                diccionario.pop(accion)
    
    def is_terminal(self, line):
        variable = line[0]
        if variable[0] == "t" and variable[1:].isdigit():
            return False
        return True

    def eliminar_acciones_repetidas(self, inroute, auxfile):
        with open(inroute, "r") as infile, open(auxfile, "w+") as outfile:
            self.findventanas_oportunidad(infile)
            acciones = dict()
            sustitutos = dict()
            cod = infile.readlines()
            infile.seek(0)
            for index, line in enumerate(cod, start=1):
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    sustituido = False
                    for i in range(1, len(linevector)):
                        if linevector[i] in sustitutos:
                            linevector[i] = sustitutos[linevector[i]]
                            sustituido = True
                    if len(linevector) > 1 and linevector[1] == "=":
                        accion = " ".join(linevector[2:])
                        variable = linevector[0]
                        if self.is_terminal(linevector):
                            self.limpiar_diccionario(acciones, variable)
                        elif not sustituido:
                            if accion in acciones:
                                sustitutos[variable] = acciones[accion]
                                continue
                            else:
                                acciones[accion] = variable
                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                outfile.write(" ".join(linevector) + "\n")
                self.control_eliminacion(index, acciones, sustitutos)

    def propagacion_de_constantes(self, auxfile, outroute):
        with open(auxfile, "r") as infile, open(outroute, "w+") as outfile:
            self.findventanas_oportunidad(infile)
            valores = dict()
            cod = infile.readlines()
            for index, line in enumerate(cod, start=1):
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    sustituido = False
                    for i in range(1, len(linevector)):
                        if linevector[i] in valores:
                            linevector[i] = valores[linevector[i]]
                            sustituido = True
                            if self.is_terminal(linevector[0]):
                                myvar = self.tabla.buscar_global(linevector[0])
                                if isinstance(myvar, Variable) and myvar.tipoDato == "INT":
                                    linevector[i] = str(int(float(linevector[i])))
                    if len(linevector) > 1 and linevector[1] == "=" and not sustituido:
                        if len(linevector) == 3 and self.is_numeric_value(linevector[-1]):
                            valores[linevector[0]] = linevector[2]
                            if not self.is_terminal(linevector):
                                continue
                        elif len(linevector) > 3 and self.is_numeric_value(linevector[2]) and self.is_numeric_value(linevector[4]):
                            try:
                                resul = eval(" ".join(linevector[2:]))
                            except ZeroDivisionError:
                                logging.error(f"Error durante optimizacion: Division por cero detectada en línea: {' '.join(linevector)}")
                                return  # o continue, según el contexto
                            if type(resul) == bool:
                                resul = 1 if resul else 0
                            del linevector[2:]
                            linevector.append(str(resul))
                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                outfile.write(" ".join(linevector) + "\n")
                self.control_propagacion(index, valores)

    def eliminar_lineas_vacias(self, archivo):
        """
        Elimina las líneas vacías de un archivo dado.
        """
        with open(archivo, "r") as f:
            lineas = f.readlines()
        with open(archivo, "w") as f:
            for linea in lineas:
                if linea.strip():  # Solo escribe si la línea no está vacía
                    f.write(linea)