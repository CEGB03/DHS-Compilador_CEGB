from compiladoresVisitor import compiladoresVisitor
from compiladoresParser import compiladoresParser
import os

class Temporales:
    def __init__(self):
        self.counter = 0
        self.stack = []
        self.tipos = {}  # Mapear temporales a tipos

    def next_temporal(self, tipo="int"):
        """Generar temporal con tipo específico"""
        temporal = f't{self.counter}'
        self.tipos[temporal] = tipo
        self.counter += 1
        return temporal

    def next_temporal_with_type(self, operando1, operando2, operacion):
        """Generar temporal inferiendo el tipo de la operación"""
        tipo_resultado = self.inferir_tipo_operacion(operando1, operando2, operacion)
        return self.next_temporal(tipo_resultado)

    def inferir_tipo_operacion(self, op1, op2, operacion):
        """Inferir tipo del resultado de una operación"""
        # Reglas básicas de inferencia de tipos
        if operacion in ['&&', '||', '==', '!=', '<', '>', '<=', '>=']:
            return "bool"
        elif any(x in [op1, op2] for x in ['double', 'float']) or \
             ('.' in str(op1)) or ('.' in str(op2)):
            return "double"
        else:
            return "int"

    def get_tipo(self, temporal):
        """Obtener tipo de un temporal"""
        return self.tipos.get(temporal, "int")

class Etiquetas:
    def __init__(self):
        self.counter = 0
        self.funciones = dict()
    
    def next_etiqueta(self):
        etiqueta = f'l{self.counter}'
        self.counter += 1
        return etiqueta

    def etiqueta_funcion(self, identificador:str):
        if identificador in self.funciones:
            return self.funciones[identificador]
        lista = []
        etiqueta1 = self.next_etiqueta()
        etiqueta2 = self.next_etiqueta()
        lista.append(etiqueta1)
        lista.append(etiqueta2)
        self.funciones[identificador] = lista
        return lista

class Walker (compiladoresVisitor):
    def __init__(self): 
        self.file = None
        self.ruta = './output/codigoIntermedio.txt'
        self.temps = Temporales()
        self.labels = Etiquetas()
        self.temporales = []  # Lista para temporales (compatibilidad con código existente)
        self.isFuncion = 0
        self.inFuncion = 0
        self.indent_level = 0
        # Pilas para manejo de expresiones de izquierda a derecha
        self.expression_stack = []  # Pila principal para expresiones
        self.operator_stack = []    # Pila para operadores
        self.temp_results = []      # Resultados temporales

    def separateBlock(self):
        """Separar bloques de código para mejor legibilidad"""
        self.file.write('\n')

    def visitPrograma(self, ctx: compiladoresParser.ProgramaContext):
        if os.path.exists("./output/Errores&Warnings.txt"):
            with open("./output/Errores&Warnings.txt") as errfile:
                if "ERROR" in errfile.read():
                    print("\033[1;31m"+"--- No se generó ningún código intermedio por errores ---"+"\033[0m")
                    return
        print("=-"*20)
        print("\033[1;32m"+"--- Generando código intermedio ---"+"\033[0m")
        self.file = open(self.ruta, "w")
        
        # ===== CORRECCIÓN: Verificar que instrucciones() existe =====
        if ctx.instrucciones():
            self.visit(ctx.instrucciones())
        else:
            #print("DEBUG: No hay instrucciones para procesar")
            pass
    
        self.file.close()
        with open(self.ruta, "r") as file:
            content = file.read()
            if content:
                print("\033[1;32m"+"--- Código intermedio generado exitosamente ---"+"\033[0m")
            else:
                print("\033[1;31m"+"--- No se generó ningún código intermedio ---"+"\033[0m")

    def visitInstrucciones(self, ctx:compiladoresParser.InstruccionesContext):
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if hasattr(child, 'accept'):
                self.visit(child)
        return

    def visitInstruccion(self, ctx: compiladoresParser.InstruccionContext):
        if ctx.declaracion():
            self.visit(ctx.declaracion())
        elif ctx.iwhile():
            self.visit(ctx.iwhile())
        elif ctx.bloque():
            self.visit(ctx.bloque())
        elif ctx.ifor():
            self.visit(ctx.ifor())
        elif ctx.iif():
            self.visit(ctx.iif())
        elif ctx.asignacion():
            self.visit(ctx.asignacion())
        elif ctx.ifuncion():
            self.visit(ctx.ifuncion())
        elif ctx.ireturn():
            self.visit(ctx.ireturn())
        elif ctx.illamada():
            self.visit(ctx.illamada())
        elif ctx.iprototipo():
            self.visit(ctx.iprototipo())

    def visitAsignacion(self, ctx: compiladoresParser.AsignacionContext):
        """Manejar asignaciones de todos los tipos de datos"""
        if ctx.asignacionNum():
            asignacion_num_ctx = ctx.asignacionNum()
            variable = asignacion_num_ctx.ID().getText()
            # ===== NUEVO: SIEMPRE generar temporal =====
            resultado = self.visit(asignacion_num_ctx.exp())
            if self.es_literal(resultado):
                temp = self.temps.next_temporal()
                self.write(f'{temp} = {resultado}')
                #self.write(f'{variable} = {temp}')
            else:
                self.write(f'{variable} = {resultado}')
            return resultado
        elif ctx.asignacionBool():
            asignacion_bool_ctx = ctx.asignacionBool()
            variable = asignacion_bool_ctx.ID().getText()
            # ===== NUEVO: SIEMPRE generar temporal =====
            resultado = self.visit(asignacion_bool_ctx.opbool())
            if self.es_literal(resultado):
                temp = self.temps.next_temporal()
                self.write(f'{temp} = {resultado}')
                #self.write(f'{variable} = {temp}')
            else:
                self.write(f'{variable} = {resultado}')
            return resultado
        else:
            self.write('// ERROR: Asignación desconocida')
            return None

    def visitE(self, ctx: compiladoresParser.EContext, left=None):
        """Procesar operaciones de suma y resta con evaluación completa"""
        if ctx.SUMA():
            # ===== CAMBIO: Asegurar que siempre se genere temporal =====
            right = self.visit(ctx.term())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} + {right}')
            # Continuar con más operaciones si existen
            if ctx.e():
                return self.visitE(ctx.e(), temp)
            return temp
        elif ctx.RESTA():
            right = self.visit(ctx.term())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} - {right}')
            if ctx.e():
                return self.visitE(ctx.e(), temp)
            return temp
        return left

    def visitInot(self, ctx: compiladoresParser.InotContext):
        left = self.visit(ctx.comp())
        if ctx.n():
            return self.visitN(ctx.n(), left)
        return left

    def visitN(self, ctx: compiladoresParser.NContext, left=None):
        # n : NOT comp n | IGUAL comp n | 
        if ctx.NOT():
            right = self.visit(ctx.comp())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = !{right}')
            # Si hay más NOT encadenados
            if ctx.n():
                return self.visitN(ctx.n(), temp)
            return temp
        elif ctx.IGUAL():
            right = self.visit(ctx.comp())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} == {right}')
            # Si hay más IGUAL encadenados
            if ctx.n():
                return self.visitN(ctx.n(), temp)
            return temp
        return left

    def visitComp(self, ctx: compiladoresParser.CompContext):
        left = self.visit(ctx.op())
        if ctx.c():
            return self.visitC(ctx.c(), left)
        return left

    def visitC(self, ctx: compiladoresParser.CContext, left=None):
        # c : MAYOR op c | MENOR op c | MAI op c | MEI op c |
        if ctx.MAYOR():
            right = self.visit(ctx.op())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} > {right}')
            if ctx.c():
                return self.visitC(ctx.c(), temp)
            return temp
        elif ctx.MENOR():
            right = self.visit(ctx.op())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} < {right}')
            if ctx.c():
                return self.visitC(ctx.c(), temp)
            return temp
        elif ctx.MAI():
            right = self.visit(ctx.op())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} >= {right}')
            if ctx.c():
                return self.visitC(ctx.c(), temp)
            return temp
        elif ctx.MEI():
            right = self.visit(ctx.op())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} <= {right}')
            if ctx.c():
                return self.visitC(ctx.c(), temp)
            return temp
        return left

    def visitOp(self, ctx: compiladoresParser.OpContext):
        left = self.visit(ctx.term())
        if left is None:
            left = "error_var"
        if ctx.e():
            return self.visitE(ctx.e(), left)
        return left

    def visitTerm(self, ctx: compiladoresParser.TermContext):
        """Procesar términos con generación inmediata de temporales"""
        left_result = self.visit(ctx.factor())
        
        # ===== CAMBIO: Si hay operaciones T, generar temporal inmediatamente =====
        if ctx.t() and ctx.t().getChildCount() > 0:
            return self.visitT(ctx.t(), left_result)
        else:
            # ===== CAMBIO: Incluso para factores simples, considerar temporal =====
            # Solo si es una expresión compleja, generar temporal
            return left_result

    def visitT(self, ctx: compiladoresParser.TContext, left=None):
        """Procesar operaciones de multiplicación/división/módulo"""
        if ctx.MULT():
            right = self.visit(ctx.factor())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} * {right}')
            if ctx.t():
                return self.visitT(ctx.t(), temp)
            return temp
        elif ctx.DIV():
            right = self.visit(ctx.factor())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} / {right}')
            if ctx.t():
                return self.visitT(ctx.t(), temp)
            return temp
        elif ctx.MOD():
            right = self.visit(ctx.factor())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} % {right}')
            if ctx.t():
                return self.visitT(ctx.t(), temp)
            return temp
        return left

    def visitFactor(self, ctx: compiladoresParser.FactorContext):
        # Caso: número entero
        if ctx.NUMERO():
            return ctx.NUMERO().getText()
        # Caso: número decimal
        elif ctx.DECIMAL():
            return ctx.DECIMAL().getText()
        # Caso: identificador (variable)
        elif ctx.ID():
            return ctx.ID().getText()
        # Caso: character
        elif ctx.CARACTER():
            return ctx.CARACTER().getText()
        # Caso: literal booleano TRUE
        elif ctx.getToken(compiladoresParser.TRUE, 0):
            return "TRUE"
        # Caso: literal booleano FALSE
        elif ctx.getToken(compiladoresParser.FALSE, 0):
            return "FALSE"
        # Caso: expresión entre paréntesis
        elif ctx.PA():
            # Expresión entre paréntesis
            return self.visit(ctx.exp())
        # Caso: llamada a función
        elif ctx.illamada():
            return self.visit(ctx.illamada())
        else:
            self.write('// ERROR: Factor desconocido')
            return "error_factor"

    def visitOpal(self, ctx: compiladoresParser.OpalContext):
        exp_ctx = ctx.exp()
        return self.visit(exp_ctx)

    def visitExp(self, ctx: compiladoresParser.ExpContext):
        return self.visit(ctx.lor())
   
    def visitLor(self, ctx: compiladoresParser.LorContext):
        left = self.visit(ctx.land())
        if ctx.a():
            return self.visitA(ctx.a(), left)
        return left

    def visitA(self, ctx: compiladoresParser.AContext, left=None):
        # a : OR land a | 
        if ctx.OR():
            right = self.visit(ctx.land())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} || {right}')
            # Si hay más OR encadenados
            if ctx.a():
                return self.visitA(ctx.a(), temp)
            return temp
        return left

    def visitLand(self, ctx: compiladoresParser.LandContext):
        # land -> inot l
        left = self.visit(ctx.inot())
        if ctx.l():
            return self.visitL(ctx.l(), left)
        return left

    def visitL(self, ctx: compiladoresParser.LContext, left=None):
        # l : AND inot l | 
        if ctx.AND():
            right = self.visit(ctx.inot())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} && {right}')
            # Si hay más AND encadenados
            if ctx.l():
                return self.visitL(ctx.l(), temp)
            return temp
        return left

    def visitIreturn(self, ctx: compiladoresParser.IreturnContext):
        if self.inFuncion == 1:
            # ===== CORRECCIÓN: Evaluar la expresión de retorno =====
            if ctx.opal():
                resultado = self.visit(ctx.opal())
                # Si es un literal, generar temporal
                if self.es_literal(resultado):
                    temp = self.temps.next_temporal()
                    self.write(f'{temp} = {resultado}')
                    self.file.write(f'push {temp}\n')
                else:
                    self.file.write(f'push {resultado}\n')
            else:
                # Return sin valor
                self.file.write(f'push 0\n')

    def visitIif(self, ctx:compiladoresParser.IifContext):
        self.visit(ctx.cond())
        temp_cond = self.temporales.pop() if len(self.temporales) > 0 else "error_cond"
        etiqueta_else = self.labels.next_etiqueta()
        self.file.write(f'ifnjmp {temp_cond}, {etiqueta_else}\n')
        etiqueta_fin = None
        self.indent_level += 1
        self.visit(ctx.instruccion())
        self.indent_level -= 1
        if ctx.ielse():
            etiqueta_fin = self.labels.next_etiqueta()
            self.file.write(f'jmp {etiqueta_fin}\n')
            self.file.write(f'label {etiqueta_else}\n')
            self.indent_level += 1
            self.visit(ctx.ielse())
            self.indent_level -= 1
            self.file.write(f'label {etiqueta_fin}\n')
        else:
            self.file.write(f'label {etiqueta_else}\n')

    def visitIwhile(self, ctx: compiladoresParser.IwhileContext):
        etiqueta_inicio = self.labels.next_etiqueta()
        etiqueta_fin = self.labels.next_etiqueta()
        self.file.write(f'label {etiqueta_inicio}\n')
        self.indent_level += 1
        temp_cond = self.visit(ctx.cond())
        if temp_cond is None and len(self.temporales) > 0:
            temp_cond = self.temporales.pop()
        self.file.write(f'ifnjmp {temp_cond}, {etiqueta_fin}\n')
        self.visit(ctx.instruccion())
        self.file.write(f'jmp {etiqueta_inicio}\n')
        self.indent_level -= 1
        self.file.write(f'label {etiqueta_fin}\n')
    
    def visitIfor(self, ctx: compiladoresParser.IforContext):
        etiqueta_inicio = self.labels.next_etiqueta()
        etiqueta_fin = self.labels.next_etiqueta()
        self.visit(ctx.init())
        self.file.write(f'label {etiqueta_inicio}\n')
        self.visit(ctx.cond())
        temp_cond = self.temporales.pop() if len(self.temporales) > 0 else "error_cond"
        self.file.write(f'ifnjmp {temp_cond}, {etiqueta_fin}\n')
        self.visit(ctx.instruccion())
        self.visit(ctx.iter())
        self.file.write(f'jmp {etiqueta_inicio}\n')
        self.file.write(f'label {etiqueta_fin}\n')

    def visitIllamada(self, ctx: compiladoresParser.IllamadaContext):
        function_name = ctx.ID().getText()
        # Extraer argumentos de la llamada
        args = self.extraer_argumentos_llamada(ctx.argumento())
        
        # ===== CORRECCIÓN: Manejo más claro de llamadas =====
        # Empujar argumentos en orden normal (se sacan en orden inverso)
        for arg in args:
            self.file.write(f'push {arg}\n')
        
        # Obtener etiquetas de función
        etiquetas = self.labels.etiqueta_funcion(function_name)
        
        # Empujar dirección de retorno y saltar
        self.file.write(f'push {etiquetas[1]}\n')
        self.file.write(f'jmp {etiquetas[0]}\n')
        self.file.write(f'label {etiquetas[1]}\n')
        
        # El resultado de la función se obtiene de la pila
        temp = self.temps.next_temporal()
        self.file.write(f'pop {temp}\n')
        return temp

    def extraer_argumentos_llamada(self, argumentos_ctx):
        """Extrae todos los argumentos de una llamada a función"""
        args = []
        if argumentos_ctx is None:
            return args
        
        # Caso base: solo un argumento
        if argumentos_ctx.opal():
            arg = self.visit(argumentos_ctx.opal())
            args.append(arg)
        
        # Caso recursivo: opal C argumento
        if argumentos_ctx.C():
            siguiente = argumentos_ctx.argumento()
            if siguiente:
                args += self.extraer_argumentos_llamada(siguiente)
        
        return args

    def visitDeclaracion(self, ctx:compiladoresParser.DeclaracionContext):
        tipo = ctx.tipo().getText() if ctx.tipo() else ""
        
        # Caso: tipo x; (solo declaración)
        if ctx.ID():
            nombre = ctx.ID().getText()
            self.write(f'{tipo} {nombre}')
            
        # Caso: tipo x = valor; (declaración con inicialización)
        elif ctx.asignacion():
            asignacion_ctx = ctx.asignacion()
            if asignacion_ctx.asignacionNum():
                nombre = asignacion_ctx.asignacionNum().ID().getText()
                # ===== CORRECCIÓN: Mostrar tipo explícitamente =====
                #self.write(f'{tipo} {nombre}')
                # ===== NUEVO: SIEMPRE generar temporal para inicializaciones =====
                resultado = self.visit(asignacion_ctx.asignacionNum().exp())
                # Si el resultado es un literal, crear temporal
                if self.es_literal(resultado):
                    temp = self.temps.next_temporal()
                    self.write(f'{temp} = {resultado}')
                    self.write(f'{nombre} = {temp}')
                else:
                    self.write(f'{nombre} = {resultado}')
            elif asignacion_ctx.asignacionBool():
                nombre = asignacion_ctx.asignacionBool().ID().getText()
                # ===== CORRECCIÓN: Mostrar tipo explícitamente =====
                #self.write(f'{tipo} {nombre}')
                # ===== NUEVO: SIEMPRE generar temporal para inicializaciones booleanas =====
                resultado = self.visit(asignacion_ctx.asignacionBool().opbool())
                if self.es_literal(resultado):
                    temp = self.temps.next_temporal()
                    self.write(f'{temp} = {resultado}')
                    self.write(f'{nombre} = {temp}')
                else:
                    self.write(f'{nombre} = {resultado}')

        # ===== CORRECCIÓN: Declaraciones múltiples dentro del método =====
        if ctx.dec():
            self.visit(ctx.dec())

    def visitDec(self, ctx: compiladoresParser.DecContext):
        """Procesar declaraciones múltiples como double a, b=5.5, c;"""
        if ctx.C():
            # ===== CORRECCIÓN: Obtener tipo del contexto padre =====
            tipo_padre = self.get_tipo_contexto_actual(ctx)
            
            if ctx.ID():
                # Caso: , variable
                nombre = ctx.ID().getText()
                self.write(f'{tipo_padre} {nombre}')
            elif ctx.asignacion():
                # Caso: , variable = valor
                asignacion_ctx = ctx.asignacion()
                if asignacion_ctx.asignacionNum():
                    nombre = asignacion_ctx.asignacionNum().ID().getText()
                    self.write(f'{tipo_padre} {nombre}')
                    resultado = self.visit(asignacion_ctx.asignacionNum().exp())
                    if self.es_literal(resultado):
                        temp = self.temps.next_temporal()
                        self.write(f'{temp} = {resultado}')
                        self.write(f'{nombre} = {temp}')
                    else:
                        self.write(f'{nombre} = {resultado}')
                elif asignacion_ctx.asignacionBool():
                    nombre = asignacion_ctx.asignacionBool().ID().getText()
                    self.write(f'{tipo_padre} {nombre}')
                    resultado = self.visit(asignacion_ctx.asignacionBool().opbool())
                    if self.es_literal(resultado):
                        temp = self.temps.next_temporal()
                        self.write(f'{temp} = {resultado}')
                        self.write(f'{nombre} = {temp}')
                    else:
                        self.write(f'{nombre} = {resultado}')
            
            # Procesar siguiente declaración
            if ctx.dec():
                self.visit(ctx.dec())

    def visitBloque(self, ctx: compiladoresParser.BloqueContext):
        # ===== CORRECCIÓN: Verificar que instrucciones() existe =====
        if ctx.instrucciones():
            self.visit(ctx.instrucciones())
        else:
            print("DEBUG: Bloque sin instrucciones")

    def visitIfuncion(self, ctx: compiladoresParser.IfuncionContext):
        function_name = ctx.ID().getText() if ctx.ID() else "anonymous"
        etiquetas = self.labels.etiqueta_funcion(function_name)
        
        self.file.write(f'label {etiquetas[0]}\n')
        self.file.write(f'pop t0\n')  # Dirección de retorno
        
        # ===== CORRECCIÓN: Procesar argumentos correctamente =====
        argumentos_funcion = []
        if ctx.param():
            argumentos_funcion = self.extraer_argumentos_param(ctx.param())
            # Procesar argumentos en orden inverso (como vienen de la pila)
            for tipo, nombre in reversed(argumentos_funcion):
                self.file.write(f'pop {nombre}\n')
                # ===== CAMBIO: NO escribir tipo en código intermedio =====

        # Procesar declaraciones de variables locales
        self.inFuncion = 1
        self.visit(ctx.bloque())
        self.inFuncion = 0
        
        self.file.write(f'jmp t0\n')  # Retorno

    def extraer_argumentos_param(self, param_ctx):
        """Extrae argumentos de la definición de función"""
        args = []
        ctx = param_ctx
        
        # Verificar si hay un 'p' directamente
        if hasattr(ctx, 'p') and ctx.p():
            tipo = ctx.p().tipo().getText()
            nombre = ctx.p().ID().getText()
            args.append((tipo, nombre))
        
        # Navegación recursiva
        while ctx is not None and hasattr(ctx, 'param') and ctx.param():
            ctx = ctx.param()
            if hasattr(ctx, 'p') and ctx.p():
                tipo = ctx.p().tipo().getText()
                nombre = ctx.p().ID().getText()
                args.append((tipo, nombre))
            else:
                break
        
        return args

    def visitIelse(self, ctx: compiladoresParser.IelseContext):
        self.visit(ctx.instruccion())

    def visitCond(self, ctx: compiladoresParser.CondContext):
        return self.visit(ctx.opal())

    def visitErrorNode(self, node):
        self.write('// ERROR: Nodo de error sintáctico')
        print(f"---- ERROR EN NODO: {node.getText()} ----")
        return super().visitErrorNode(node)

    def write(self, text):
        """Escribir línea al archivo de código intermedio"""
        if self.file:
            self.file.write(text + '\n')
        else:
            print(f"WARNING: Trying to write without file: {text}")

    def get_tipo_contexto_actual(self, ctx):
        """Obtener el tipo de dato del contexto actual de declaración"""
        # Navegar hacia el padre para encontrar el tipo
        parent = ctx.parentCtx
        while parent:
            if hasattr(parent, 'tipo') and parent.tipo():
                return parent.tipo().getText()
            parent = parent.parentCtx
        return "int"  # Tipo por defecto

    def es_literal(self, valor):
        """Determina si un valor es un literal (número, booleano, etc.)"""
        if not valor:
            return False
        valor_str = str(valor).strip()
        # Es literal si es número, decimal, TRUE, FALSE
        return (valor_str.replace('.', '').replace('-', '').isdigit() or 
                valor_str in ['TRUE', 'FALSE', 'true', 'false'])

    def visitOpbool(self, ctx: compiladoresParser.OpboolContext):
        """Procesar expresiones booleanas"""
        left = self.visit(ctx.factorBool())
        if ctx.bools():
            return self.visitBools(ctx.bools(), left)
        return left

    def visitBools(self, ctx: compiladoresParser.BoolsContext, left=None):
        """Procesar operadores booleanos encadenados"""
        if ctx.OR():
            right = self.visit(ctx.opbool())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} || {right}')
            return temp
        elif ctx.AND():
            right = self.visit(ctx.opbool())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} && {right}')
            return temp
        return left

    def visitFactorBool(self, ctx: compiladoresParser.FactorBoolContext):
        """Procesar factores booleanos"""
        if ctx.TRUE():
            return "TRUE"
        elif ctx.FALSE():
            return "FALSE"
        elif ctx.ID():
            return ctx.ID().getText()
        elif ctx.PA():
            # Expresión booleana entre paréntesis
            return self.visit(ctx.opbool())
        return "error_bool"