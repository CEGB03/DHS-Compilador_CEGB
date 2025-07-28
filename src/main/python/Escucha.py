# Escucha.py
import re
import logging
from antlr4 import ErrorNode, TerminalNode
from compiladoresListener import compiladoresListener
from compiladoresParser import compiladoresParser
from Squeleton import *

logging.basicConfig(level=logging.DEBUG)

class Escucha(compiladoresListener):
    numTokens = 0
    numNodos = 0
    tabla = TablaSimbolos.get_instancia()
    error = False

    def __init__(self):
        self.log_file = open('./output/Compilacion.txt', 'a', encoding='utf-8')
        self.nivel_indentacion = 0
        # Pila de control de tipos para expresiones
        self.type_stack = []
        # Control de contexto de condiciones
        self.in_condition = False
        # Control de contexto de asignación
        self.in_assignment = False
        self.in_declaration = False
        
        # ===== NUEVO: Variables para manejo de funciones =====
        self.nombre_funcion_actual = None
        self.tipo_funcion_actual = None
        self.argumentos_funcion_actual = []
        self.lectura_argumentos = False
        self.en_funcion = False

    def write_log(self, mensaje, indentar=True):
        if indentar:
            self.log_file.write('\t' * self.nivel_indentacion + mensaje + '\n')
        else:
            self.log_file.write(mensaje + '\n')
        self.log_file.flush()

    def __del__(self):
        if hasattr(self, 'log_file'):
            self.log_file.close()

    def enterPrograma(self, ctx: compiladoresParser.ProgramaContext):
        self.write_log("Comienza la compilacion", indentar=False)

    def exitPrograma(self, ctx: compiladoresParser.ProgramaContext):
        self.write_log("Fin de la compilacion\n\n", indentar=False)
        
        # ===== CORRECCIÓN: Asegurar que el contexto global esté en el historial =====
        # Mover el contexto global al historial si no está
        if self.tabla.contextos and self.tabla.contextos[0] not in self.tabla.contextos_historial:
            contexto_global = self.tabla.contextos[0]
            if contexto_global.nombreContexto == "Global":
                self.tabla.contextos_historial.insert(0, contexto_global)
        
        # Marcar main como usada ANTES del reporte
        for contexto in self.tabla.contextos + self.tabla.contextos_historial:
            for id in contexto.ids.values():
                if isinstance(id, Funcion) and id.nombre == "main":
                    id.set_usado()
                    #print("DEBUG: ✓ main marcada como usada antes del reporte")
                    break
        
        self.write_log(self.tabla.__str__(), indentar=False)
        self.tabla.reporte_variables_y_funciones_sin_usar()
        self.tabla.del_Contexto()

    # ─────────────────────────────────────────────
    # BLOQUES / CONTEXTO
    # ─────────────────────────────────────────────
    def enterBloque(self, ctx: compiladoresParser.BloqueContext):
        self.write_log("{", indentar=True)
        self.nivel_indentacion += 1
        if not self.en_funcion:
            self.tabla.add_contexto("BLOQUE")

    def exitBloque(self, ctx: compiladoresParser.BloqueContext):
        self.nivel_indentacion -= 1
        self.write_log("}", indentar=True)
        if not self.en_funcion:
            self.tabla.del_Contexto()

    # ─────────────────────────────────────────────
    # PROTOTIPOS DE FUNCIONES
    # ─────────────────────────────────────────────
    def exitIprototipo(self, ctx: compiladoresParser.IprototipoContext):
        linea = ctx.start.line
        tipo_retorno = ctx.tipo().getText() if ctx.tipo() else ""
        nombre_funcion = ctx.ID().getText() if ctx.ID() else ""
        
        args = []
        if ctx.protoparam():
            args = self.extraer_argumentos_unified(ctx.protoparam())

        funcion = Funcion(nombre_funcion, tipo_retorno)
        funcion.set_args(args)
        funcion.prototipado = True
        funcion.inicializado = False
        
        busquedaLocal = self.tabla.buscar_local(nombre_funcion)
        busquedaGlobal = self.tabla.buscar_global(nombre_funcion)
        
        if busquedaLocal is None and busquedaGlobal is None:
            # ===== CORRECCIÓN: Asegurar que se agregue al contexto global =====
            #print(f"DEBUG: Agregando prototipo {nombre_funcion} al contexto: {self.tabla.contextos[-1].nombreContexto}")
            self.tabla.add_identificador(funcion)
            self.write_log(f"Declarada Función: {funcion.tipoDato} {nombre_funcion}: Prototipado? True en línea {linea}", indentar=True)
            self.write_log(f"Argumentos:  {funcion.args}", indentar=True)
        else:
            self.write_log(f"Advertencia: redeclarada función {funcion.tipoDato} {nombre_funcion}: Prototipado? True en línea {linea}", indentar=True)
            print("\033[1;33m" + f"Línea {linea}: Advertencia: La función '{nombre_funcion}' es redeclarada en el contexto actual." + "\033[0m")

    # ─────────────────────────────────────────────
    # DECLARACIÓN DE FUNCIONES
    # ─────────────────────────────────────────────
    def enterIfuncion(self, ctx: compiladoresParser.IfuncionContext):
        # Crear contexto para la función
        self.tabla.add_contexto("BLOQUE_FUNCION")
        self.write_log("def funcion", indentar=True)
        self.nivel_indentacion += 1
        self.en_funcion = True
        
        # ===== NUEVO: Inicializar variables de función =====
        self.argumentos_funcion_actual = []
        self.lectura_argumentos = True
        
        # Obtener información básica de la función
        if ctx.ID():
            self.nombre_funcion_actual = ctx.ID().getText()
            self.tabla.renombrar_contexto_actual(self.nombre_funcion_actual)
            #logging.debug(f"DEBUG: Procesando función {self.nombre_funcion_actual}")
        
        if ctx.tipo():
            self.tipo_funcion_actual = ctx.tipo().getText()

    def exitIfuncion(self, ctx: compiladoresParser.IfuncionContext):
        # ===== CORRECCIÓN: Obtener nombre real de la función =====
        if ctx.ID():
            nombre_funcion = ctx.ID().getText()
        else:
            nombre_funcion = "BLOQUE_FUNCION"
    
        linea = ctx.start.line
    
        if ctx.tipo():
            tipo_retorno = ctx.tipo().getText()
        else:
            tipo_retorno = ""
    
        # Asegurar que el contexto tenga el nombre correcto
        self.tabla.renombrar_contexto_actual(nombre_funcion)
        
        # ===== NUEVO: Procesar argumentos extraídos =====
        args = []
        if ctx.param():
            args = self.extraer_argumentos_param(ctx.param())
        
        # Verificar si existe prototipo y validar
        funcion = self.tabla.buscar_global(nombre_funcion)
        if funcion and isinstance(funcion, Funcion):
            if funcion.prototipado and not funcion.inicializado:
                # Verificar correspondencia de parámetros con prototipo
                if not self.verificar_correspondencia_parametros(funcion.args, args, linea):
                    self.error = True
                else:
                    funcion.prototipado = True
                    funcion.inicializado = True
                    funcion.set_args(args)
                    self.write_log(f"Línea {linea}: Definición de función '{nombre_funcion}' completada.", indentar=True)
            else:
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: La función '{nombre_funcion}' ya está definida.", indentar=True)
                self.error = True
        else:
            # Nueva función sin prototipo
            funcion = Funcion(nombre_funcion, tipo_retorno)
            funcion.set_args(args)
            funcion.prototipado = False
            funcion.inicializado = True
            self.tabla.add_identificador(funcion)
            self.write_log(f"Línea {linea}: Definición de función '{nombre_funcion}' agregada.", indentar=True)
        
        # ===== NUEVO: Marcar main como usada automáticamente =====
        if nombre_funcion.lower() == "main":
            if funcion and isinstance(funcion, Funcion):
                funcion.set_usado()
                self.write_log(f"Línea {linea}: Función 'main' marcada automáticamente como usada.", indentar=True)
    
        # Limpiar variables de función
        self.nombre_funcion_actual = None
        self.tipo_funcion_actual = None
        self.argumentos_funcion_actual = []
        self.lectura_argumentos = False
        
        self.nivel_indentacion -= 1
        self.write_log("// EXIT FUNCION", indentar=True)
        self.en_funcion = False
        self.tabla.del_Contexto()

    # ─────────────────────────────────────────────
    # PROCESAMIENTO DE PARÁMETROS EN enterParam/exitP
    # ─────────────────────────────────────────────
    def enterParam(self, ctx: compiladoresParser.ParamContext):
        """Iniciar lectura de parámetros"""
        self.lectura_argumentos = True

    def exitP(self, ctx: compiladoresParser.PContext):
        """Procesar cada parámetro individual"""
        if self.lectura_argumentos and ctx.tipo() and ctx.ID():
            tipo = ctx.tipo().getText()
            identificador = ctx.ID().getText()
            
            # Agregar a la lista de argumentos
            self.argumentos_funcion_actual.append((tipo, identificador))
            #logging.debug(f"DEBUG: Encontrado argumento: {tipo} {identificador}")
            
            # ===== CRUCIAL: Registrar inmediatamente como variable =====
            if self.tabla.buscar_local(identificador) is None:
                var_arg = Variable(identificador, tipo, inicializado=True, declarado=True)
                self.tabla.add_identificador(var_arg)
                self.write_log(f"Argumento agregado: {tipo} {identificador}", indentar=True)
                #logging.debug(f"DEBUG: ✓ Argumento {identificador} registrado en contexto")
            else:
                #logging.debug(f"DEBUG: ⚠️ Argumento {identificador} ya existe en el contexto")
                pass

    def exitParam(self, ctx: compiladoresParser.ParamContext):
        """Finalizar lectura de parámetros"""
        self.lectura_argumentos = False
        
        # Verificar que se agregaron correctamente
        if self.tabla.contextos:
            contexto_actual = self.tabla.contextos[-1]
            #logging.debug(f"DEBUG: Variables en contexto {self.nombre_funcion_actual or 'FUNCION'}: {list(contexto_actual.ids.keys())}")

    # ─────────────────────────────────────────────
    # MÉTODOS DE EXTRACCIÓN DE ARGUMENTOS (compatibilidad)
    # ─────────────────────────────────────────────
    def extraer_argumentos_unified(self, param_ctx):
        """Método unificado para extraer argumentos de param o protoparam"""
        args = []
        ctx = param_ctx
        
        #logging.debug(f"DEBUG: extraer_argumentos_unified llamado con contexto: {type(ctx)}")
        
        # Para param: verificar si hay un 'p' directamente
        if hasattr(ctx, 'p') and ctx.p():
            tipo = ctx.p().tipo().getText()
            nombre = ctx.p().ID().getText()
            args.append((tipo, nombre))
            #logging.debug(f"DEBUG: Encontrado argumento directo: {tipo} {nombre}")

        # Para protoparam: verificar si hay tipo e ID directamente
        elif hasattr(ctx, 'tipo') and ctx.tipo() and hasattr(ctx, 'ID') and ctx.ID():
            tipo = ctx.tipo().getText()
            nombre = ctx.ID().getText()
            args.append((tipo, nombre))
            #logging.debug(f"DEBUG: Encontrado argumento de prototipo: {tipo} {nombre}")

        # Navegación recursiva
        while ctx is not None:
            if hasattr(ctx, 'param') and ctx.param():
                ctx = ctx.param()
                if hasattr(ctx, 'p') and ctx.p():
                    tipo = ctx.p().tipo().getText()
                    nombre = ctx.p().ID().getText()
                    args.append((tipo, nombre))
                    #logging.debug(f"DEBUG: Encontrado argumento recursivo: {tipo} {nombre}")
            elif hasattr(ctx, 'protoparam') and ctx.protoparam():
                ctx = ctx.protoparam()
                if hasattr(ctx, 'tipo') and ctx.tipo() and hasattr(ctx, 'ID') and ctx.ID():
                    tipo = ctx.tipo().getText()
                    nombre = ctx.ID().getText()
                    args.append((tipo, nombre))
                    #logging.debug(f"DEBUG: Encontrado argumento de prototipo recursivo: {tipo} {nombre}")
            else:
                break

        #logging.debug(f"DEBUG: Total argumentos extraídos: {args}")
        return args

    def extraer_argumentos_param(self, param_ctx):
        """Extrae argumentos de la definición (param)"""
        args = []
        ctx = param_ctx
        
        # Primero verificar si hay un 'p' directamente
        if hasattr(ctx, 'p') and ctx.p():
            tipo = ctx.p().tipo().getText()
            nombre = ctx.p().ID().getText()
            args.append((tipo, nombre))
        
        # Luego verificar recursivamente
        while ctx is not None and hasattr(ctx, 'param') and ctx.param():
            ctx = ctx.param()
            if hasattr(ctx, 'p') and ctx.p():
                tipo = ctx.p().tipo().getText()
                nombre = ctx.p().ID().getText()
                args.append((tipo, nombre))
        
        return args

    def verificar_correspondencia_parametros(self, params_prototipo, params_definicion, linea):
        """Verificar que los parámetros del prototipo coincidan con la definición"""
        if len(params_prototipo) != len(params_definicion):
            self.write_log(f"Línea {linea}: ERROR SEMANTICO: Cantidad de parámetros no coincide con el prototipo.")
            return False
        
        for i, (proto, defin) in enumerate(zip(params_prototipo, params_definicion)):
            if proto[0].strip().lower() != defin[0].strip().lower():
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: Tipo del parámetro {i+1} no coincide (prototipo: {proto[0]}, definición: {defin[0]}).")
                return False
        return True

    # ─────────────────────────────────────────────
    # USO DE VARIABLES
    # ─────────────────────────────────────────────
    def exitAsignacion(self, ctx):
        self.in_assignment = False
        operacion = ctx.getChild(0).getText()
        linea = ctx.start.line

        if '=' in operacion:
            nombreVariableIzquierda = operacion.split('=')[0].strip()
            expresionDerecha = operacion.split('=', 1)[1].strip()
            
            # Usar búsqueda global que incluye contextos padre
            var_izquierda = self.tabla.buscar_global(nombreVariableIzquierda)
            
            if var_izquierda is None and not self.in_declaration:
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariableIzquierda}' no fue declarada previamente.")
                logging.error(f"ERROR: Línea {linea}: Asignación a variable '{nombreVariableIzquierda}' no declarada.")
                self.error = True
                return
            
            if var_izquierda is not None:
                # Verificar variables del lado derecho
                self.verificar_variables_en_expresion(expresionDerecha, linea)
                var_izquierda.set_inicializado()
                self.write_log(f"Línea {linea}: Asignación válida: '{nombreVariableIzquierda}' = '{expresionDerecha}'.")

    def verificar_variables_en_expresion(self, expresion, linea):
        """Verificar todas las variables usadas en una expresión"""
        if expresion is None:
            return
            
        tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expresion)
        palabras_reservadas = {'TRUE', 'FALSE', 'true', 'false', 'int', 'bool', 'float', 'double', 'void', 'return', 'if', 'else', 'while', 'for'}
        
        for token in tokens:
            if token in palabras_reservadas:
                continue
                
            #logging.debug(f"DEBUG: Buscando variable '{token}' en línea {linea}")
            #logging.debug(f"DEBUG: Contextos activos: {[ctx.nombreContexto for ctx in self.tabla.contextos]}")
            
            var = self.tabla.buscar_global(token)
            
            if var and not isinstance(var, Funcion):
                var.set_usado()
                #logging.debug(f"DEBUG: ✓ Variable '{token}' encontrada y marcada como usada")
                if not var.inicializado:
                    self.write_log(f"Línea {linea}: ADVERTENCIA: La variable '{token}' se usa sin ser inicializada.")
            elif var and isinstance(var, Funcion):
                var.set_usado()
            else:
                #logging.debug(f"DEBUG: ❌ Variable '{token}' NO encontrada")
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: El identificador '{token}' no fue declarado previamente.")
                #logging.error(f"ERROR: Línea {linea}: El identificador '{token}' no fue declarado previamente.")
                self.error = True

    # ─────────────────────────────────────────────
    # RESTO DE MÉTODOS (sin cambios)
    # ─────────────────────────────────────────────
    def enterDeclaracion(self, ctx):
        self.in_declaration = True

    def exitDeclaracion(self, ctx: compiladoresParser.DeclaracionContext):
        self.in_declaration = False
        tipoDeDato = ctx.getChild(0).getText()
        linea = ctx.start.line
        declaracion = ctx.getText()
        
        sin_tipo = declaracion[len(tipoDeDato):].replace(';', '').strip()
        declaraciones = self.parsear_declaraciones_multiples(sin_tipo)
        
        for decl in declaraciones:
            nombreVariable, inicializacion, inicializado = decl
            if not self.verificar_variable_existente(nombreVariable, linea):
                variable = Variable(nombreVariable, tipoDeDato, inicializado=inicializado)
                self.tabla.add_identificador(variable)
                if inicializado:
                    variable.set_inicializado()
                    self.write_log(f"Línea {linea}: La variable '{nombreVariable}' se declaró e inicializó en el contexto actual.")
                    self.verificar_variables_en_expresion(inicializacion, linea)
                else:
                    self.write_log(f"Línea {linea}: La variable '{nombreVariable}' se declaró en el contexto actual.")

    def parsear_declaraciones_multiples(self, declaraciones_str):
        """Parsear declaraciones múltiples como 'a, b=5, c=x+y'"""
        declaraciones = []
        partes = [d.strip() for d in declaraciones_str.split(',')]
        
        for parte in partes:
            if '=' in parte:
                nombre, valor = [x.strip() for x in parte.split('=', 1)]
                declaraciones.append((nombre, valor, True))
            else:
                declaraciones.append((parte.strip(), None, False))
        
        return declaraciones

    def verificar_variable_existente(self, nombre, linea):
        """Verificar si una variable ya existe y reportar error"""
        busqueda_local = self.tabla.buscar_local(nombre)
        busqueda_global = self.tabla.buscar_global(nombre)
        
        if busqueda_local is not None:
            self.write_log(f"Línea {linea}: ERROR SEMANTICO: La variable '{nombre}' ya está declarada en el contexto local.")
            self.error = True
            return True
        elif busqueda_global is not None:
            self.write_log(f"Línea {linea}: ERROR SEMANTICO: La variable '{nombre}' ya está declarada en el contexto global.")
            self.error = True
            return True
        return False

    # Control de condiciones y otros métodos
    def enterCond(self, ctx: compiladoresParser.CondContext):
        self.in_condition = True
        self.type_stack.append([])

    def exitCond(self, ctx: compiladoresParser.CondContext):
        self.in_condition = False
        tipos = self.type_stack.pop()
        self.validar_condicion(tipos, ctx)
        self.verificar_variables_en_expresion(ctx.getText(), ctx.start.line)

    def validar_condicion(self, tipos, ctx):
        """Validar que la condición sea válida"""
        linea = ctx.start.line
        for tipo in tipos:
            if tipo not in ['bool', 'int', 'double', 'float']:
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: Tipo '{tipo}' no válido en condición.")
                self.error = True

    def enterOpal(self, ctx: compiladoresParser.OpalContext):
        if not self.in_condition and not self.in_assignment:
            self.type_stack.append([])

    def exitOpal(self, ctx: compiladoresParser.OpalContext):
        linea = ctx.start.line
        if ctx.getToken(compiladoresParser.OR, 0) or ctx.getToken(compiladoresParser.AND, 0):
            self.validar_operacion_logica(ctx, linea)

    def validar_operacion_logica(self, ctx, linea):
        """Validar operaciones lógicas (&&, ||)"""
        if ctx.getToken(compiladoresParser.AND, 0):
            self.write_log(f"Línea {linea}: Operación lógica AND detectada", indentar=True)
        elif ctx.getToken(compiladoresParser.OR, 0):
            self.write_log(f"Línea {linea}: Operación lógica OR detectada", indentar=True)
        
        texto = ctx.getText()
        self.write_log(f"Línea {linea}: Validando operación booleana: {texto}", indentar=True)

    def enterIwhile(self, ctx: compiladoresParser.IwhileContext):
        self.write_log("while (...)", indentar=True)

    def exitIwhile(self, ctx: compiladoresParser.IwhileContext):
        self.write_log("// FIN WHILE", indentar=True)
        if ctx.cond():
            expresion_cond = ctx.cond().getText()
            self.verificar_variables_en_expresion(expresion_cond, ctx.start.line)

    def enterIfor(self, ctx: compiladoresParser.IforContext):
        self.write_log("for (...)", indentar=True)

    def exitIfor(self, ctx: compiladoresParser.IforContext):
        self.write_log("// FIN FOR", indentar=True)

    def enterIif(self, ctx: compiladoresParser.IifContext):
        self.write_log("if (...)", indentar=True)

    def exitIif(self, ctx: compiladoresParser.IifContext):
        self.write_log("// EXIT IF", indentar=True)
        if ctx.cond():
            expresion_cond = ctx.cond().getText()
            self.verificar_variables_en_expresion(expresion_cond, ctx.start.line)

    def enterIelse(self, ctx: compiladoresParser.IelseContext):
        self.write_log("else", indentar=True)

    def exitIelse(self, ctx: compiladoresParser.IelseContext):
        self.write_log("// EXIT ELSE", indentar=True)

    def exitIllamada(self, ctx):
        nombreFuncion = ctx.ID().getText()
        linea = ctx.start.line
        args_ctx = ctx.argumento()
        argumentos = self.extraer_argumentos_llamada(args_ctx)
        tipos_args = self.obtener_tipos_argumentos(argumentos, linea)
        
        self.write_log(f"{nombreFuncion}({', '.join(argumentos)})", indentar=True)
        
        funcion = self.tabla.buscar_global(nombreFuncion)
        if funcion is not None and isinstance(funcion, Funcion):
            funcion.set_usado()
            self.verificar_argumentos_funcion(funcion, tipos_args, linea)
        else:
            self.write_log(f"Línea {linea}: ERROR SEMANTICO: La función '{nombreFuncion}' no fue declarada previamente.")
            self.error = True

    def obtener_tipos_argumentos(self, argumentos, linea):
        """Obtener tipos de los argumentos de una llamada a función"""
        tipos_args = []
        for arg in argumentos:
            if arg.upper() in ['TRUE', 'FALSE']:
                tipos_args.append(('bool', None))
            elif re.match(r'^\d+$', arg):
                tipos_args.append(('int', None))
            elif re.match(r'^\d+\.\d+$', arg):
                tipos_args.append(('double', None))
            else:
                var = self.tabla.buscar_global(arg)
                if var and hasattr(var, 'tipoDato'):
                    var.set_usado()
                    if not var.inicializado:
                        self.write_log(f"Línea {linea}: ADVERTENCIA: La variable '{arg}' se usa sin ser inicializada.")
                    tipos_args.append((var.tipoDato, arg))
                else:
                    self.write_log(f"Línea {linea}: ERROR SEMANTICO: El identificador '{arg}' no fue declarado previamente.")
                    self.error = True
                    tipos_args.append(('desconocido', arg))
        return tipos_args

    def verificar_argumentos_funcion(self, funcion, tipos_args, linea):
        """Verificar tipos y cantidad de argumentos de función"""
        if len(tipos_args) != len(funcion.args):
            self.write_log(f"Línea {linea}: ERROR SEMANTICO: La cantidad de argumentos no coincide (esperados: {len(funcion.args)}, recibidos: {len(tipos_args)})")
            self.error = True
            return
            
        for i, (real, esperado) in enumerate(zip(tipos_args, funcion.args)):
            tipo_real, _ = real
            tipo_esperado, _ = esperado
            if tipo_real != tipo_esperado and tipo_real != 'desconocido':
                self.write_log(f"Línea {linea}: ERROR SEMANTICO: El tipo del argumento {i+1} no coincide (esperado: {tipo_esperado}, recibido: {tipo_real})")
                self.error = True

    def enterAsignacion(self, ctx: compiladoresParser.AsignacionContext):
        self.in_assignment = True

    def extraer_argumentos_llamada(self, argumentos_ctx):
        """Extrae todos los argumentos de una llamada a función"""
        args = []
        if argumentos_ctx is None:
            return args
        if argumentos_ctx.opal():
            args.append(argumentos_ctx.opal().getText())
        if argumentos_ctx.C():
            siguiente = argumentos_ctx.argumento()
            if siguiente:
                args += self.extraer_argumentos_llamada(siguiente)
        return args

    def exitIreturn(self, ctx: compiladoresParser.IreturnContext):
        """Procesar statements de return"""
        linea = ctx.start.line
        if ctx.opal():
            expresion_return = ctx.opal().getText()
            self.verificar_variables_en_expresion(expresion_return, linea)
            self.write_log(f"Línea {linea}: Return procesado: {expresion_return}", indentar=True)

    def visitTerminal(self, node: TerminalNode):
        texto = node.getText()
        palabras_reservadas = {'TRUE', 'FALSE', 'true', 'false', 'int', 'bool', 'float', 'double', 'void', 'return', 'if', 'else', 'while', 'for'}
        
        if texto.isidentifier() and texto not in palabras_reservadas:
            variable = self.tabla.buscar_global(texto)
            if variable and not isinstance(variable, Funcion):
                if not variable.inicializado and not self.in_assignment:
                    print(f"\033[93mADVERTENCIA: La variable '{texto}' se usa sin ser inicializada.\033[0m")
        self.numTokens += 1

    def visitErrorNode(self, node: ErrorNode):
        self.write_log(" ERROR SINTACTICO", indentar=True)