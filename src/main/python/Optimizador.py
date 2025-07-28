import os
import logging
import re

from Squeleton import TablaSimbolos, Variable

class Optimizador:
    def __init__(self):
        self.ventanas = []
        self.tabla = TablaSimbolos.get_instancia()
        
    def optimizar(self):
        # ===== ARCHIVOS PARA CADA RONDA =====
        inroute = "output/codigoIntermedio.txt"
        
        # Archivos intermedios para cada pasada
        pasada1_eliminacion = "output/pasada1_eliminacion.txt"
        pasada1_propagacion = "output/pasada1_propagacion.txt"
        
        pasada2_eliminacion = "output/pasada2_eliminacion.txt"
        pasada2_propagacion = "output/pasada2_propagacion.txt"
        pasada2_valores_cocidos = "output/pasada2_valores_cocidos.txt"
        pasada2_propagacion_final = "output/pasada2_propagacion_final.txt"
        
        pasada3_eliminacion = "output/pasada3_eliminacion.txt"
        pasada3_propagacion = "output/pasada3_propagacion.txt"
        pasada3_operaciones_complejas = "output/pasada3_operaciones_complejas.txt"
        pasada3_propagacion_final = "output/pasada3_propagacion_final.txt"
        
        # Archivo final
        outroute = "output/codigoIntermedioOptimizado.txt"
        auxfile = "output/auxfile.txt"
        
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

            print("\033[1;33m--- Iniciando optimización de código intermedio (3 pasadas detalladas) ---\033[0m")
            
            # ============================================
            # PRIMERA PASADA - Eliminación inicial + Propagación
            # ============================================
            print("🔄 Pasada 1/3: Eliminación inicial + Propagación")
            
            # Paso 1.1: Eliminación de acciones repetidas
            print("   📋 1.1 - Eliminando acciones repetidas...")
            self.eliminar_acciones_repetidas(inroute, pasada1_eliminacion)
            self.eliminar_lineas_vacias(pasada1_eliminacion)
            print(f"   ✅ Resultado guardado en: {pasada1_eliminacion}")
            
            # Paso 1.2: Propagación de constantes
            print("   📋 1.2 - Propagando constantes...")
            self.propagacion_de_constantes_mejorada(pasada1_eliminacion, pasada1_propagacion)
            self.eliminar_lineas_vacias(pasada1_propagacion)
            print(f"   ✅ Resultado guardado en: {pasada1_propagacion}")

            # ============================================
            # SEGUNDA PASADA - Re-optimización completa
            # ============================================
            print("🔄 Pasada 2/3: Re-optimización completa")
            
            # Paso 2.1: Eliminación mejorada de acciones repetidas
            print("   📋 2.1 - Eliminación mejorada de acciones repetidas...")
            self.eliminar_acciones_repetidas_mejorada(pasada1_propagacion, pasada2_eliminacion)
            self.eliminar_lineas_vacias(pasada2_eliminacion)
            print(f"   ✅ Resultado guardado en: {pasada2_eliminacion}")
            
            # Paso 2.2: Propagación de constantes
            print("   📋 2.2 - Propagando constantes...")
            self.propagacion_de_constantes_mejorada(pasada2_eliminacion, pasada2_propagacion)
            self.eliminar_lineas_vacias(pasada2_propagacion)
            print(f"   ✅ Resultado guardado en: {pasada2_propagacion}")
            
            # Paso 2.3: Reemplazar valores cocidos
            print("   📋 2.3 - Reemplazando valores cocidos...")
            self.reemplazar_valores_cocidos(pasada2_propagacion, pasada2_valores_cocidos)
            self.eliminar_lineas_vacias(pasada2_valores_cocidos)
            print(f"   ✅ Resultado guardado en: {pasada2_valores_cocidos}")
            
            # Paso 2.4: Propagación final de pasada 2
            print("   📋 2.4 - Propagación final de pasada 2...")
            self.propagacion_de_constantes_mejorada(pasada2_valores_cocidos, pasada2_propagacion_final)
            self.eliminar_lineas_vacias(pasada2_propagacion_final)
            print(f"   ✅ Resultado guardado en: {pasada2_propagacion_final}")

            # ============================================
            # TERCERA PASADA - Optimización final
            # ============================================
            print("🔄 Pasada 3/3: Optimización final")
            
            # Paso 3.1: Eliminación final de acciones repetidas
            print("   📋 3.1 - Eliminación final de acciones repetidas...")
            self.eliminar_acciones_repetidas_mejorada(pasada2_propagacion_final, pasada3_eliminacion)
            self.eliminar_lineas_vacias(pasada3_eliminacion)
            print(f"   ✅ Resultado guardado en: {pasada3_eliminacion}")
            
            # Paso 3.2: Propagación de constantes
            print("   📋 3.2 - Propagando constantes...")
            self.propagacion_de_constantes_mejorada(pasada3_eliminacion, pasada3_propagacion)
            self.eliminar_lineas_vacias(pasada3_propagacion)
            print(f"   ✅ Resultado guardado en: {pasada3_propagacion}")
            
            # Paso 3.3: Optimizar operaciones complejas
            print("   📋 3.3 - Optimizando operaciones complejas...")
            self.optimizar_operaciones_complejas(pasada3_propagacion, pasada3_operaciones_complejas)
            self.eliminar_lineas_vacias(pasada3_operaciones_complejas)
            print(f"   ✅ Resultado guardado en: {pasada3_operaciones_complejas}")
            
            # Paso 3.4: Propagación final
            print("   📋 3.4 - Propagación final...")
            self.propagacion_de_constantes_mejorada(pasada3_operaciones_complejas, pasada3_propagacion_final)
            self.eliminar_lineas_vacias(pasada3_propagacion_final)
            print(f"   ✅ Resultado guardado en: {pasada3_propagacion_final}")

            # ============================================
            # POSTPROCESADO FINAL
            # ============================================
            print("🔄 Postprocesado final...")
            
            # Limpiar comentarios del último archivo
            self.eliminar_comentarios(pasada3_propagacion_final)
            
            # Leer el código optimizado de la última pasada
            with open(pasada3_propagacion_final, "r") as f:
                codigo = f.readlines()

            # Aplicar las optimizaciones extra
            print("   📋 Aplicando simplificación de condiciones...")
            codigo = self.simplificacion_condiciones(codigo)
            
            print("   📋 Aplicando propagación de copias...")
            codigo = self.propagacion_de_copias(codigo)

            # Guardar el resultado final
            with open(outroute, "w") as f:
                for linea in codigo:
                    f.write(linea if linea.endswith('\n') else linea + '\n')

            # ============================================
            # RESUMEN DE ARCHIVOS GENERADOS
            # ============================================
            print(f"\n\033[1;32m✓ Optimización completada exitosamente!\033[0m")
            print(f"\n📁 Archivos generados por pasada:")
            print(f"   \033[1;36mPasada 1:\033[0m")
            print(f"     • {pasada1_eliminacion}")
            print(f"     • {pasada1_propagacion}")
            print(f"   \033[1;36mPasada 2:\033[0m")
            print(f"     • {pasada2_eliminacion}")
            print(f"     • {pasada2_propagacion}")
            print(f"     • {pasada2_valores_cocidos}")
            print(f"     • {pasada2_propagacion_final}")
            print(f"   \033[1;36mPasada 3:\033[0m")
            print(f"     • {pasada3_eliminacion}")
            print(f"     • {pasada3_propagacion}")
            print(f"     • {pasada3_operaciones_complejas}")
            print(f"     • {pasada3_propagacion_final}")
            print(f"   \033[1;32mFinal:\033[0m {outroute}")
            
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

    def eliminar_acciones_repetidas_mejorada(self, input_file, output_file):
        """Eliminar acciones repetidas pero mantener temporales necesarios"""
        try:
            with open(input_file, 'r') as f:
                lineas = f.readlines()
            
            lineas_unicas = []
            temporales_usados = set()
            
            # ===== PASO 1: Identificar qué temporales se usan =====
            for linea in lineas:
                linea_limpia = linea.strip()
                # Buscar temporales que se usan en el lado derecho
                import re
                temporales_en_linea = re.findall(r'\bt\d+\b', linea_limpia)
                temporales_usados.update(temporales_en_linea)
            
            # ===== PASO 2: Mantener definiciones de temporales usados =====
            for linea in lineas:
                linea_limpia = linea.strip()
                if not linea_limpia or linea_limpia.startswith('//'):
                    lineas_unicas.append(linea)
                    continue
                
                # Si es definición de temporal usado, mantenerla
                if '=' in linea_limpia:
                    var = linea_limpia.split('=')[0].strip()
                    if var.startswith('t') and var in temporales_usados:
                        lineas_unicas.append(linea)
                        continue
                
                # Para otras líneas, mantener si no están duplicadas
                if linea not in lineas_unicas:
                    lineas_unicas.append(linea)
            
            with open(output_file, 'w') as f:
                f.writelines(lineas_unicas)
                
        except Exception as e:
            print(f"Error en eliminación de acciones repetidas: {e}")

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

    def propagacion_de_constantes_mejorada(self, input_file, output_file):
        """Propagar constantes de forma más cuidadosa"""
        try:
            with open(input_file, 'r') as f:
                lineas = f.readlines()
            
            variables = {}  # variable -> valor
            lineas_optimizadas = []
            
            for linea in lineas:
                linea = linea.strip()
                if not linea or linea.startswith('//'):
                    lineas_optimizadas.append(linea)
                    continue
                
                # Manejo más cuidadoso de asignaciones
                if '=' in linea and not any(op in linea for op in ['==', '!=', '<=', '>=', '<', '>']):
                    partes = linea.split('=', 1)
                    if len(partes) == 2:
                        var = partes[0].strip()
                        valor = partes[1].strip()
                        
                        # Solo propagar si es un valor literal simple
                        if self.es_valor_literal_simple(valor):
                            variables[var] = valor
                            lineas_optimizadas.append(linea)
                        else:
                            # Reemplazar variables en el valor antes de procesar
                            valor_reemplazado = self.reemplazar_variables_en_expresion(valor, variables)
                            linea_nueva = f"{var} = {valor_reemplazado}"
                            lineas_optimizadas.append(linea_nueva)
                            
                            # Si el resultado es literal, guardarlo para futuras propagaciones
                            if self.es_valor_literal_simple(valor_reemplazado):
                                variables[var] = valor_reemplazado
                    else:
                        lineas_optimizadas.append(linea)
                else:
                    # Reemplazar variables en otras líneas
                    linea_reemplazada = self.reemplazar_variables_en_expresion(linea, variables)
                    lineas_optimizadas.append(linea_reemplazada)
            
            with open(output_file, 'w') as f:
                for linea in lineas_optimizadas:
                    f.write(linea + '\n')
                    
        except Exception as e:
            print(f"Error en propagación de constantes: {e}")
        
    def es_valor_literal_simple(self, valor):
        """Verificar si un valor es un literal simple (número, booleano)"""
        valor = valor.strip()
        # Es literal si es número, decimal, TRUE, FALSE
        return (valor.replace('.', '').replace('-', '').isdigit() or 
                valor in ['TRUE', 'FALSE', 'true', 'false'])

    def reemplazar_variables_en_expresion(self, expresion, variables):
        """Reemplazar variables por sus valores en una expresión"""
        import re
        
        # ===== CORRECCIÓN: Solo reemplazar variables completas, no parciales =====
        for var, valor in variables.items():
            # Usar regex para reemplazar solo palabras completas
            patron = r'\b' + re.escape(var) + r'\b'
            expresion = re.sub(patron, valor, expresion)
        
        return expresion

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
    
    def corregir_flujo_funciones(self, input_file, output_file):
        """Corregir el flujo de control en funciones"""
        try:
            with open(input_file, 'r') as f:
                lineas = f.readlines()
            
            lineas_corregidas = []
            i = 0
            
            while i < len(lineas):
                linea = lineas[i].strip()
                
                # ===== CORRECCIÓN: Manejo de returns en funciones =====
                if linea.startswith('label') and i + 1 < len(lineas):
                    # Verificar si es una función
                    if any(lineas[j].strip().startswith('pop') for j in range(i+1, min(i+5, len(lineas)))):
                        # Es una función, corregir el return
                        lineas_corregidas.append(lineas[i])
                        i += 1
                        
                        # Procesar hasta encontrar el return
                        while i < len(lineas) and not lineas[i].strip().startswith('jmp t'):
                            linea_actual = lineas[i].strip()
                            
                            # ===== CORRECCIÓN: Asegurar push antes de cada return =====
                            if i + 1 < len(lineas) and lineas[i+1].strip().startswith('jmp t'):
                                # Próxima línea es return, asegurar push
                                if not linea_actual.startswith('push'):
                                    # Buscar el último temporal definido
                                    for j in range(i-1, max(0, i-10), -1):
                                        linea_prev = lineas[j].strip()
                                        if '=' in linea_prev and linea_prev.split('=')[0].strip().startswith('t'):
                                            temporal = linea_prev.split('=')[0].strip()
                                            lineas_corregidas.append(f"push {temporal}\n")
                                            break
                            
                            lineas_corregidas.append(lineas[i])
                            i += 1
                            
                        # Agregar la línea de return
                        if i < len(lineas):
                            lineas_corregidas.append(lineas[i])
                            i += 1
                    else:
                        lineas_corregidas.append(lineas[i])
                        i += 1
                else:
                    lineas_corregidas.append(lineas[i])
                    i += 1
            
            with open(output_file, 'w') as f:
                f.writelines(lineas_corregidas)
                
        except Exception as e:
            print(f"Error en corrección de flujo de funciones: {e}")
    
    def findventanas_oportunidad(self, infile):
        """
        Encuentra ventanas de oportunidad para optimización
        """
        try:
            # Leer archivo y resetear puntero
            infile.seek(0)
            lineas = infile.readlines()
            infile.seek(0)
            
            # Análisis básico de ventanas de optimización
            ventanas = []
            for i, linea in enumerate(lineas):
                linea_limpia = linea.strip()
                if '=' in linea_limpia and not any(op in linea_limpia for op in ['==', '!=', '<=', '>=']):
                    ventanas.append(i)
            
            self.ventanas = ventanas
            print(f"📊 Encontradas {len(ventanas)} ventanas de optimización")
            
        except Exception as e:
            print(f"Error en findventanas_oportunidad: {e}")
            self.ventanas = []
    
    def control_eliminacion(self, index, acciones, sustitutos):
        """Control para eliminación de acciones repetidas"""
        # Control cada 50 líneas
        if index % 50 == 0:
            print(f"   🔄 Procesando línea {index}...")

    def control_propagacion(self, index, valores):
        """Control para propagación de constantes"""
        # Control cada 50 líneas
        if index % 50 == 0:
            print(f"   🔄 Propagando línea {index}...")

    def is_terminal(self, variable):
        """Verificar si es una variable terminal (temporal)"""
        return variable.startswith('t') and variable[1:].isdigit()

    def is_numeric_value(self, value):
        """Verificar si un valor es numérico"""
        try:
            float(value.replace('TRUE', '1').replace('FALSE', '0'))
            return True
        except ValueError:
            return False

    def limpiar_diccionario(self, diccionario, variable):
        """Limpiar diccionario de una variable específica"""
        diccionario_copy = diccionario.copy()
        for clave in diccionario_copy:
            if variable in clave:
                diccionario.pop(clave)