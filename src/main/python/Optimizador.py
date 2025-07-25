import os
import logging
import re

from Squeleton import TablaSimbolos, Variable

class Optimizador:
    def __init__(self):
        self.ventanas = []
        self.tabla = TablaSimbolos.get_instancia()
        
    def optimizar(self):
        auxfile = "output/auxfile.txt"
        inroute = "output/codigoIntermedio.txt"
        outroute = "output/codigoIntermedioOptimizado.txt"
        
        # Verificar existencia del archivo de entrada
        if not os.path.exists(inroute):
            print(f"\033[1;31mError: No se encuentra el archivo {inroute}\033[0m")
            return False
            
        # Asegurar que el directorio de salida existe
        os.makedirs(os.path.dirname(auxfile), exist_ok=True)
        
        try:
            self.eliminar_comentarios(inroute)
            self.eliminar_tabulaciones(inroute)
            self.eliminar_indentacion(inroute)

            print("\033[1;33m--- Iniciando optimización de código intermedio (3 pasadas) ---\033[0m")
            
            # PRIMERA VUELTA - Optimización completa
            print("🔄 Pasada 1/3: Eliminación inicial + Propagación")
            self.eliminar_acciones_repetidas(inroute, auxfile)
            self.propagacion_de_constantes_mejorada(auxfile, outroute)
            self.eliminar_lineas_vacias(outroute)
            self.eliminar_lineas_vacias(auxfile)

            # SEGUNDA VUELTA - Tratar como si fuera la primera
            print("🔄 Pasada 2/3: Re-optimización completa")
            self.eliminar_acciones_repetidas_mejorada(outroute, auxfile)
            self.propagacion_de_constantes_mejorada(auxfile, outroute)
            self.reemplazar_valores_cocidos(outroute, auxfile)
            self.propagacion_de_constantes_mejorada(auxfile, outroute)
            self.eliminar_lineas_vacias(outroute)
            self.eliminar_lineas_vacias(auxfile)

            # TERCERA VUELTA - Optimización final
            print("🔄 Pasada 3/3: Optimización final")
            self.eliminar_acciones_repetidas_mejorada(outroute, auxfile)
            self.propagacion_de_constantes_mejorada(auxfile, outroute)
            self.optimizar_operaciones_complejas(outroute, auxfile)
            self.propagacion_de_constantes_mejorada(auxfile, outroute)
            self.eliminar_lineas_vacias(outroute)
            
            # Limpiar comentarios
            self.eliminar_comentarios(outroute)
            # --- POSTPROCESADO FINAL ---
            # Leer el código optimizado
            with open(outroute, "r") as f:
                codigo = f.readlines()

            # Aplicar las optimizaciones extra
            #codigo = self.eliminacion_codigo_inalcanzable(codigo)
            codigo = self.simplificacion_condiciones(codigo)
            codigo = self.propagacion_de_copias(codigo)

            # Guardar el resultado final
            with open(outroute, "w") as f:
                for linea in codigo:
                    f.write(linea if linea.endswith('\n') else linea + '\n')

            print(f"\033[1;32m✓ Optimización completada exitosamente en: {outroute}\033[0m")
            return True
            
        except Exception as e:
            print(f"\033[1;31mError durante optimización: {str(e)}\033[0m")
            print(f"Detalles del error: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    def reemplazar_valores_cocidos(self, inroute, outroute):
        """
        Reemplaza valores inicializados que no son alterados
        """
        with open(inroute, "r") as infile, open(outroute, "w") as outfile:
            self.findventanas_oportunidad(infile)
            valores_cocidos = {}  # Variables con valores fijos
            alterados = set()     # Variables que fueron modificadas
            
            cod = infile.readlines()
            
            # Primera pasada: identificar valores cocidos y alteraciones
            for line in cod:
                linevector = line.split()
                if len(linevector) > 2 and linevector[1] == "=":
                    variable = linevector[0]
                    
                    # Si es una asignación directa de constante
                    if (len(linevector) == 3 and 
                        self.is_numeric_value(linevector[2]) and
                        self.is_terminal(variable)):
                        
                        if variable not in alterados:
                            valores_cocidos[variable] = linevector[2]
                        else:
                            # Ya fue alterada, remover de cocidos
                            valores_cocidos.pop(variable, None)
                    else:
                        # Cualquier otra asignación marca como alterada
                        alterados.add(variable)
                        valores_cocidos.pop(variable, None)
            
            # Segunda pasada: aplicar reemplazos
            for line in cod:
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    
                    # Reemplazar valores cocidos en toda la línea
                    if len(linevector) > 2 and linevector[1] == "=":
                        for i in range(2, len(linevector)):
                            if linevector[i] in valores_cocidos:
                                linevector[i] = valores_cocidos[linevector[i]]
                    
                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                        
                outfile.write(" ".join(linevector) + "\n")

    def optimizar_operaciones_complejas(self, inroute, outroute):
        """
        Optimiza operaciones complejas como y = a + s + f + q + f * ea - as / as
        """
        with open(inroute, "r") as infile, open(outroute, "w") as outfile:
            self.findventanas_oportunidad(infile)
            
            cod = infile.readlines()
            operaciones_complejas = {}  # Mapea expresiones complejas
            
            for line in cod:
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    
                    # Detectar y optimizar operaciones complejas
                    if (len(linevector) > 4 and linevector[1] == "=" and
                        self.contiene_operacion_compleja(linevector[2:])):
                        
                        expresion = " ".join(linevector[2:])
                        variable = linevector[0]
                        
                        # Intentar simplificar la expresión compleja
                        expresion_simplificada = self.simplificar_expresion_compleja(expresion)
                        
                        if expresion_simplificada != expresion:
                            # La expresión fue simplificada
                            linevector = [variable, "="] + expresion_simplificada.split()
                            print(f"🔧 Operación compleja optimizada: {expresion} → {expresion_simplificada}")

                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                    
                outfile.write(" ".join(linevector) + "\n")

    def contiene_operacion_compleja(self, tokens):
        """
        Detecta si una secuencia de tokens contiene una operación compleja
        """
        operadores = {'+', '-', '*', '/', '%'}
        operador_count = sum(1 for token in tokens if token in operadores)
        return operador_count >= 3  # 3 o más operadores = operación compleja

    def simplificar_expresion_compleja(self, expresion):
        """
        Simplifica expresiones complejas aplicando reglas matemáticas
        """
        try:
            # Evaluar si toda la expresión son constantes
            tokens = expresion.split()
            all_numeric = True
            
            for i, token in enumerate(tokens):
                if i % 2 == 0:  # Posiciones pares deben ser números
                    if not self.is_numeric_value(token):
                        all_numeric = False
                        break
                else:  # Posiciones impares deben ser operadores
                    if token not in {'+', '-', '*', '/', '%'}:
                        all_numeric = False
                        break
            
            if all_numeric:
                # Toda la expresión son constantes, evaluarla
                resultado = eval(expresion)
                if isinstance(resultado, bool):
                    resultado = 1 if resultado else 0
                return str(resultado)
            else:
                # Aplicar simplificaciones algebraicas básicas
                return self.aplicar_simplificaciones_algebraicas(expresion)
                
        except:
            return expresion  # Si hay error, devolver expresión original

    def aplicar_simplificaciones_algebraicas(self, expresion):
        """
        Aplica simplificaciones algebraicas básicas
        """
        # Simplificaciones como: x + 0 = x, x * 1 = x, x * 0 = 0, etc.
        expresion = re.sub(r'\b(\w+)\s*\+\s*0\b', r'\1', expresion)  # x + 0 = x
        expresion = re.sub(r'\b0\s*\+\s*(\w+)\b', r'\1', expresion)  # 0 + x = x
        expresion = re.sub(r'\b(\w+)\s*\*\s*1\b', r'\1', expresion)  # x * 1 = x
        expresion = re.sub(r'\b1\s*\*\s*(\w+)\b', r'\1', expresion)  # 1 * x = x
        expresion = re.sub(r'\b(\w+)\s*\*\s*0\b', '0', expresion)    # x * 0 = 0
        expresion = re.sub(r'\b0\s*\*\s*(\w+)\b', '0', expresion)    # 0 * x = 0
        expresion = re.sub(r'\b(\w+)\s*-\s*0\b', r'\1', expresion)   # x - 0 = x
        
        return expresion

    def eliminar_acciones_repetidas_mejorada(self, inroute, auxfile):
        """
        Versión mejorada que considera patrones más complejos de repetición
        """
        with open(inroute, "r") as infile, open(auxfile, "w") as outfile:
            self.findventanas_oportunidad(infile)
            acciones = {}  # expresión → variable que la contiene
            sustitutos = {}  # variable → su equivalente optimizado
            expresiones_complejas = {}  # Para operaciones de múltiples pasos
            
            cod = infile.readlines()
            infile.seek(0)
            
            for index, line in enumerate(cod, start=1):
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    
                    # Sustituir variables por sus equivalentes
                    sustituido = False
                    for i in range(2, len(linevector)):
                        if linevector[i] in sustitutos:
                            linevector[i] = sustitutos[linevector[i]]
                            sustituido = True
                    
                    # Procesar asignaciones
                    if len(linevector) > 1 and linevector[1] == "=":
                        accion = " ".join(linevector[2:])
                        variable = linevector[0]
                        
                        # Generar clave normalizada para la acción
                        accion_normalizada = self.normalizar_expresion(accion)
                        
                        if self.is_terminal(variable):
                            # Variables terminales invalidan temporales relacionados
                            self.limpiar_diccionario_mejorado(acciones, variable)
                            self.limpiar_diccionario_mejorado(expresiones_complejas, variable)
                        elif not sustituido:
                            # Buscar expresión equivalente
                            if accion_normalizada in acciones:
                                sustitutos[variable] = acciones[accion_normalizada]
                                continue  # No escribir esta línea
                            else:
                                acciones[accion_normalizada] = variable
                                # Para operaciones complejas, también guardar la original
                                if self.contiene_operacion_compleja(accion.split()):
                                    expresiones_complejas[accion] = variable
                    
                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                    
                outfile.write(" ".join(linevector) + "\n")
                self.control_eliminacion(index, acciones, sustitutos)

    def normalizar_expresion(self, expresion):
        """
        Normaliza expresiones para detectar equivalencias
        Ejemplo: "a + b" y "b + a" se normalizan igual
        """
        tokens = expresion.split()
        
        # Para operaciones simples binarias, normalizar orden
        if len(tokens) == 3 and tokens[1] in ['+', '*']:
            # Operaciones conmutativas: ordenar operandos
            if tokens[0] > tokens[2]:
                return f"{tokens[2]} {tokens[1]} {tokens[0]}"
        
        return expresion

    def limpiar_diccionario_mejorado(self, diccionario, valor):
        """
        Versión mejorada que limpia más efectivamente
        """
        diccionario_copy = diccionario.copy()
        for clave in diccionario_copy:
            # Buscar la variable en cualquier parte de la expresión
            if re.search(r'\b' + re.escape(valor) + r'\b', clave):
                diccionario.pop(clave)

    def propagacion_de_constantes_mejorada(self, auxfile, outroute):
        """
        Versión mejorada de propagación de constantes con mejor manejo de tipos
        """
        with open(auxfile, "r") as infile, open(outroute, "w") as outfile:
            self.findventanas_oportunidad(infile)
            valores = {}  # variable → valor constante
            tipos_variables = {}  # variable → tipo de dato
            
            cod = infile.readlines()
            
            for index, line in enumerate(cod, start=1):
                linevector = line.split()
                if len(linevector) > 0:
                    if linevector[0] == "ifnjmp":
                        linevector[1] = linevector[1][:-1]
                    
                    # Sustituir valores conocidos
                    sustituido = False
                    for i in range(2, len(linevector)):
                        if linevector[i] in valores:
                            linevector[i] = valores[linevector[i]]
                            sustituido = True
                            
                            # Ajustar tipo si es necesario
                            if len(linevector) > 0 and self.is_terminal(linevector[0]):
                                myvar = self.tabla.buscar_global(linevector[0])
                                if isinstance(myvar, Variable):
                                    tipos_variables[linevector[0]] = myvar.tipoDato
                                    if myvar.tipoDato == "int":
                                        try:
                                            linevector[i] = str(int(float(linevector[i])))
                                        except:
                                            pass
                    
                    # Procesar nuevas asignaciones
                    if len(linevector) > 1 and linevector[1] == "=" and not sustituido:
                        variable = linevector[0]
                        
                        # Asignación de constante simple
                        if len(linevector) == 3 and self.is_numeric_value(linevector[2]):
                            valores[variable] = linevector[2]
                            if not self.is_terminal(variable):
                                continue
                        
                        # Operación entre constantes
                        elif (len(linevector) > 3 and 
                                all(self.is_numeric_value(linevector[i]) for i in range(2, len(linevector), 2))):
                            try:
                                # Evaluar toda la expresión
                                expresion = " ".join(linevector[2:])
                                resultado = eval(expresion)
                                
                                # Manejar resultado booleano
                                if isinstance(resultado, bool):
                                    resultado = 1 if resultado else 0
                                
                                # Aplicar tipo si se conoce
                                if variable in tipos_variables and tipos_variables[variable] == "int":
                                    resultado = int(resultado)
                                
                                valores[variable] = str(resultado)
                                
                                # Reemplazar línea con resultado
                                linevector = [variable, "=", str(resultado)]
                                
                            except ZeroDivisionError:
                                print(f"\033[1;33m⚠️  División por cero detectada en línea {index}\033[0m")
                                # Continuar sin optimizar
                            except Exception as e:
                                # Error en evaluación, continuar sin optimizar
                                pass
                    
                    if linevector[0] == "ifnjmp":
                        linevector[1] += ","
                    
                outfile.write(" ".join(linevector) + "\n")
                self.control_propagacion(index, valores)

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
            if len(next) > 0 and next[0] == "jmp":
                if len(nnext) > 1 and nnext[0] == "label" and len(current) > 1 and nnext[1] == current[1]:
                    return True
        return False
    
    def close_ventana(self, lnum):
        if self.ventanas:
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
        i = 0
        while i < len(self.ventanas):
            ventana = self.ventanas[i]
            if len(ventana) >= 2:
                start, end = ventana[0], ventana[1]
                if currentline < end:
                    return
                if currentline == end:
                    valores.clear()
                    self.ventanas.pop(i)
                    return
            i += 1
    
    def control_eliminacion(self, currentline, acciones, sustitutos):
        i = 0
        while i < len(self.ventanas):
            ventana = self.ventanas[i]
            if len(ventana) >= 2:
                start, end = ventana[0], ventana[1]
                if currentline < end:
                    return
                if currentline == end:
                    acciones.clear()
                    sustitutos.clear()
                    self.ventanas.pop(i)
                    return
            i += 1
    
    def is_numeric_value(self, val: str):
        if not val:
            return False
        val = val.replace('.', '', 1)
        val = val.replace('-', '', 1)  # Permitir números negativos
        return val.isdigit()
    
    def limpiar_diccionario(self, diccionario, valor):
        diccionario_copy = diccionario.copy()
        for accion in diccionario_copy:
            if valor in accion:
                diccionario.pop(accion)
    
    def is_terminal(self, variable: str):
        """
        Distingue correctamente entre variables temporales y terminales
        Una variable terminal es cualquier variable que no es temporal
        """
        # Una variable temporal comienza con 't' seguido de dígitos
        return not (variable.startswith("t") and variable[1:].isdigit())

    def eliminar_acciones_repetidas(self, inroute, auxfile):
        with open(inroute, "r") as infile, open(auxfile, "w") as outfile:
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
                        if self.is_terminal(variable):
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
        with open(auxfile, "r") as infile, open(outroute, "w") as outfile:
            self.findventanas_oportunidad(infile)
            valores = dict()
            cod = infile.readlines()
            for index, line in enumerate(cod, start=1):
                lienvector = line.split()
                if len(lienvector) > 0:
                    if lienvector[0] == "ifnjmp":
                        lienvector[1] = lienvector[1][:-1]
                    sustituido = False
                    for i in range(1, len(lienvector)):
                        if lienvector[i] in valores:
                            lienvector[i] = valores[lienvector[i]]
                            sustituido = True
                            if self.is_terminal(lienvector[0]):
                                myvar = self.tabla.buscar_global(lienvector[0])
                                if isinstance(myvar, Variable) and myvar.tipoDato.lower() == "int":
                                    lienvector[i] = str(int(float(lienvector[i])))
                    if len(lienvector) > 1 and lienvector[1] == "=" and not sustituido:
                        if len(lienvector) == 3 and self.is_numeric_value(lienvector[-1]):
                            valores[lienvector[0]] = lienvector[2]
                            if not self.is_terminal(lienvector[0]):
                                continue
                        elif len(lienvector) > 3 and self.is_numeric_value(lienvector[2]) and self.is_numeric_value(lienvector[4]):
                            try:
                                resul = eval(" ".join(lienvector[2:]))
                            except ZeroDivisionError:
                                print(f"\033[1;33m⚠️  División por cero detectada en línea {index}\033[0m")
                                continue
                            if type(resul) == bool:
                                resul = 1 if resul else 0
                            del lienvector[2:]
                            lienvector.append(str(resul))
                    if lienvector[0] == "ifnjmp":
                        lienvector[1] += ","
                outfile.write(" ".join(lienvector) + "\n")
                self.control_propagacion(index, valores)

    @staticmethod
    def eliminacion_codigo_inalcanzable(codigo):
        codOptimizado = []
        etiquetas_utilizadas = set()

        # Detectar etiquetas referenciadas
        for linea in codigo:
            if 'jmp' in linea or 'ifnjmp' in linea:
                partes = linea.strip().split()
                if partes[-1].startswith('l'):
                    etiquetas_utilizadas.add(partes[-1])

        saltar = False
        for i, linea in enumerate(codigo):
            linea_strip = linea.strip()
            if linea_strip.startswith('label'):
                etiqueta = linea_strip.split()[1]
                if etiqueta in etiquetas_utilizadas or i == 0:
                    saltar = False
                    codOptimizado.append(linea)
                else:
                    saltar = True
            elif saltar:
                continue
            else:
                codOptimizado.append(linea)
        return codOptimizado

    @staticmethod
    def simplificacion_condiciones(codigo):
        codOptimizado = []
        for linea in codigo:
            if '=' in linea:
                partes = linea.strip().split('=')
                izq = partes[0].strip()
                der = partes[1].strip()

                # Simplificación booleana básica
                if '&&' in der:
                    op1, op2 = [x.strip() for x in der.split('&&')]
                    if op1 == 'TRUE' and op2 == 'TRUE':
                        codOptimizado.append(f'{izq} = TRUE')
                    elif op1 == 'FALSE' or op2 == 'FALSE':
                        codOptimizado.append(f'{izq} = FALSE')
                    elif op1 == 'TRUE':
                        codOptimizado.append(f'{izq} = {op2}')
                    elif op2 == 'TRUE':
                        codOptimizado.append(f'{izq} = {op1}')
                    else:
                        codOptimizado.append(linea)

                elif '||' in der:
                    op1, op2 = [x.strip() for x in der.split('||')]
                    if op1 == 'TRUE' or op2 == 'TRUE':
                        codOptimizado.append(f'{izq} = TRUE')
                    elif op1 == 'FALSE' and op2 == 'FALSE':
                        codOptimizado.append(f'{izq} = FALSE')
                    elif op1 == 'FALSE':
                        codOptimizado.append(f'{izq} = {op2}')
                    elif op2 == 'FALSE':
                        codOptimizado.append(f'{izq} = {op1}')
                    else:
                        codOptimizado.append(linea)
                else:
                    codOptimizado.append(linea)
            else:
                codOptimizado.append(linea)
        return codOptimizado

    @staticmethod
    def propagacion_de_copias(codigo):
        codOptimizado = []
        copias = {}

        for linea in codigo:
            linea_strip = linea.strip()
            if '=' in linea_strip and not any(op in linea_strip for op in ['+', '-', '*', '/', '&&', '||', '==', '!=', '<', '>', '<=', '>=']):
                partes = linea_strip.split('=')
                izq = partes[0].strip()
                der = partes[1].strip()

                if der in copias:
                    copias[izq] = copias[der]
                else:
                    copias[izq] = der
                codOptimizado.append(linea)
            else:
                nueva_linea = linea
                for var in copias:
                    reemplazo = copias[var]
                    # Solo reemplaza variables completas, no subcadenas
                    nueva_linea = Optimizador.reemplazo_variables(nueva_linea, var, reemplazo)
                codOptimizado.append(nueva_linea)
        return codOptimizado


    @staticmethod
    def reemplazo_variables(linea, var, valor):
        import re
        # Solo reemplaza si la variable es una palabra completa (\b)
        patron = r'\b' + re.escape(var) + r'\b'
        return re.sub(patron, valor, linea)

    
    def eliminar_lineas_vacias(self, archivo):
        """
        Elimina las líneas vacías de un archivo dado.
        """
        try:
            with open(archivo, "r") as f:
                lineas = f.readlines()
            with open(archivo, "w") as f:
                for linea in lineas:
                    if linea.strip():  # Solo escribe si la línea no está vacía
                        f.write(linea)
        except Exception as e:
            print(f"\033[1;33m⚠️  Error eliminando líneas vacías de {archivo}: {str(e)}\033[0m")
    
    def eliminar_comentarios(self, archivo):
        """
        Elimina todas las líneas que empiecen con // del archivo especificado
        """
        try:
            with open(archivo, "r") as f:
                lineas = f.readlines()
            
            # Filtrar líneas que no empiecen con //
            lineas_sin_comentarios = []
            comentarios_eliminados = 0
            
            for linea in lineas:
                linea_stripped = linea.strip()
                if linea_stripped.startswith("//"):
                    comentarios_eliminados += 1
                else:
                    lineas_sin_comentarios.append(linea)
            
            # Escribir de vuelta el archivo sin comentarios
            with open(archivo, "w") as f:
                f.writelines(lineas_sin_comentarios)
            
            if comentarios_eliminados > 0:
                print(f"🧹 Eliminados {comentarios_eliminados} comentarios del código optimizado")
            
        except Exception as e:
            print(f"\033[1;33m⚠️  Error eliminando comentarios de {archivo}: {str(e)}\033[0m")

    def eliminar_tabulaciones(self, archivo):
        """
        Elimina todas las tabulaciones de un archivo dado.
        """
        try:
            with open(archivo, "r") as f:
                lineas = f.readlines()
            with open(archivo, "w") as f:
                for linea in lineas:
                    f.write(linea.replace('\t', ''))
        except Exception as e:
            print(f"\033[1;33m⚠️  Error eliminando tabulaciones de {archivo}: {str(e)}\033[0m")
    def eliminar_indentacion(self, archivo):
        """
        Elimina toda la indentación (tabulaciones y espacios al inicio) de cada línea de un archivo.
        """
        try:
            with open(archivo, "r") as f:
                lineas = f.readlines()
            with open(archivo, "w") as f:
                for linea in lineas:
                    f.write(linea.lstrip())  # Elimina espacios y tabs al inicio
        except Exception as e:
            print(f"\033[1;33m⚠️  Error eliminando indentación de {archivo}: {str(e)}\033[0m")