from compiladoresVisitor import compiladoresVisitor
from compiladoresParser import compiladoresParser
import os

class Temporales:
    def __init__(self):
        self.counter = 0
        self.stack = []  # Pila para manejar temporales
    
    def next_temporal(self):
        temporal = f't{self.counter}'
        self.counter += 1
        return temporal
    
    def push(self, temp):
        self.stack.append(temp)
    
    def pop(self):
        return self.stack.pop() if self.stack else None
    
    def peek(self):
        return self.stack[-1] if self.stack else None

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
        # ===== CAMBIO: Removida la generación de inicializaciones globales separada =====
        self.visit(ctx.instrucciones())
        self.file.close()
        with open(self.ruta, "r") as file:
            content = file.read()
            if content:
                print("\033[1;32m"+"--- Código intermedio generado exitosamente ---"+"\033[0m")
            else:
                print("\033[1;31m"+"--- No se generó ningún código intermedio ---"+"\033[0m")

    def visitInstrucciones(self, ctx:compiladoresParser.InstruccionesContext):
        self.visit(ctx.instruccion())
        if ctx.instrucciones().getChildCount() != 0:
            self.visit(ctx.instrucciones())
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
        # Determinar si es asignacionNum o asignacionBool
        if ctx.asignacionNum():
            asignacion_num_ctx = ctx.asignacionNum()
            variable = asignacion_num_ctx.ID().getText()
            # Procesar la expresión numérica
            temporal = self.visit(asignacion_num_ctx.exp())
            self.write(f'{variable} = {temporal}')
            self.write(f'// Asignación numérica: {variable}')
            return temporal
        elif ctx.asignacionBool():
            asignacion_bool_ctx = ctx.asignacionBool()
            variable = asignacion_bool_ctx.ID().getText()
            # Procesar la expresión booleana
            temporal = self.visit(asignacion_bool_ctx.opbool())
            self.write(f'{variable} = {temporal}')
            self.write(f'// Asignación booleana: {variable}')
            return temporal
        else:
            self.write('// ERROR: Asignación desconocida')
            return None

    def visitE(self, ctx: compiladoresParser.EContext):
        if ctx.SUMA():
            left_result = self.visit(ctx.term()) if ctx.term() else None
            right_result = self.visit(ctx.e()) if ctx.e() else None
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left_result} + {right_result}')
            self.write(f'// Operación resuelta: {left_result} + {right_result}')
            return temp
        elif ctx.RESTA():
            left_result = self.visit(ctx.term()) if ctx.term() else None
            right_result = self.visit(ctx.e()) if ctx.e() else None
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left_result} - {right_result}')
            self.write(f'// Operación resuelta: {left_result} - {right_result}')
            return temp
        elif ctx.term():
            return self.visit(ctx.term())
        return None

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

    def visitE(self, ctx: compiladoresParser.EContext, left=None):
        if ctx.SUMA():
            right = self.visit(ctx.term())
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {left} + {right}')
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

    def visitTerm(self, ctx: compiladoresParser.TermContext):
        """===== MEJORADO: Procesamiento de términos con resolución inmediata ====="""
        # Procesar factor
        left_result = self.visit(ctx.factor())
        
        # Si hay operaciones de multiplicación/división
        if ctx.t().getChildCount() != 0:
            # Guardar resultado izquierdo
            self.expression_stack.append(left_result)
            
            # Procesar operaciones t
            result = self.visit(ctx.t())
            
            return result if result else left_result
        else:
            return left_result

    def visitT(self, ctx: compiladoresParser.TContext, left=None):
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
            value = ctx.NUMERO().getText()
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {value}')
            self.write(f'// Literal: {value}')
            return temp
        # Caso: número decimal
        elif ctx.DECIMAL():
            value = ctx.DECIMAL().getText()
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {value}')
            self.write(f'// Literal: {value}')
            return temp
        # Caso: identificador (variable)
        elif ctx.ID():
            varname = ctx.ID().getText()
            # Verifica si la variable existe en la tabla de símbolos (opcional)
            # Si no existe, retorna un string especial y escribe un comentario de error
            # if not self.tabla.buscar_global(varname):
            #     self.write(f'// ERROR: Variable {varname} no declarada')
            #     return "error_var"
            return varname
        # Caso: character
        elif ctx.CARACTER():
            value = ctx.CARACTER().getText()
            temp = self.temps.next_temporal()
            self.write(f'{temp} = {value}')
            self.write(f'// Literal: {value}')
            return temp
        # Caso: literal booleano TRUE
        elif ctx.getToken(compiladoresParser.TRUE, 0):
            temp = self.temps.next_temporal()
            self.write(f'{temp} = 1')
            self.write(f'// Literal: TRUE')
            return temp
        # Caso: literal booleano FALSE
        elif ctx.getToken(compiladoresParser.FALSE, 0):
            temp = self.temps.next_temporal()
            self.write(f'{temp} = 0')
            self.write(f'// Literal: FALSE')
            return temp
        # Caso: expresión entre paréntesis
        elif ctx.PA():
            return self.visit(ctx.exp())
        # Caso: llamada a función
        elif ctx.illamada():
            result = self.visit(ctx.illamada())
            if result is None:
                self.write(f'// ERROR: Llamada a función no válida')
                return "error_func"
            return result
        else:
            self.write(f'// ERROR: Factor no reconocido')
            return "error_factor"

    def visitOpcomp(self, ctx):
        """===== CORREGIDO: Mejor manejo de comparaciones con temporales ====="""
        left = ctx.ID().getText()
        operator = ctx.comps().getText()
        
        # Procesar factor derecho correctamente
        factor_result = self.visit(ctx.factor())
        
        temp = self.temps.next_temporal()
        self.file.write(f"{temp} = {left} {operator} {factor_result}\n")
        self.temporales.append(temp)
        self.write(f'// Comparación: {left} {operator} {factor_result}')
        return temp

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
            resultado = self.visit(ctx.opal())
            self.file.write(f'push {resultado}\n')

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
        self.write(f'// Llamada a función: {function_name}')
        for arg in reversed(args):
            self.file.write(f'push {arg}\n')
            self.write(f'// Argumento: {arg}')
        etiquetas = self.labels.etiqueta_funcion(function_name)
        self.file.write(f'push {etiquetas[1]}\n')
        self.file.write(f'jmp {etiquetas[0]}\n')
        self.file.write(f'label {etiquetas[1]}\n')
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
        # Caso: int x;
        if ctx.ID():
            nombre = ctx.ID().getText()
            self.write(f'{tipo} {nombre}')
        # Caso: int x = 1; o int x = ...;
        elif ctx.asignacion():
            asignacion_ctx = ctx.asignacion()
            # Puede ser asignacionNum o asignacionBool
            if asignacion_ctx.asignacionNum():
                nombre = asignacion_ctx.asignacionNum().ID().getText()
            elif asignacion_ctx.asignacionBool():
                nombre = asignacion_ctx.asignacionBool().ID().getText()
            else:
                nombre = "??"
            resultado = self.visit(ctx.asignacion())
            # Aquí se conecta el temporal con la variable
            #self.write(f'{nombre} = {resultado}')
        # Declaraciones múltiples
        if ctx.dec():
            self.visit(ctx.dec())

    def visitInit(self, ctx: compiladoresParser.InitContext):
        # Usar asignacion() directamente según tu gramática
        if ctx.asignacion():
            self.visit(ctx.asignacion())

    def visitBloque(self, ctx: compiladoresParser.BloqueContext):
        self.visit(ctx.instrucciones())

    def visitIfuncion(self, ctx: compiladoresParser.IfuncionContext):
        args = []

        def extraer_argumentos(param_ctx):
            if param_ctx is None:
                return
            # param : p C param | p
            if param_ctx.p():
                tipo = param_ctx.p().tipo().getText()
                nombre = param_ctx.p().ID().getText()
                args.append((tipo, nombre))
                if param_ctx.C():
                    extraer_argumentos(param_ctx.param())
            # Si param está vacío, no hacer nada

        extraer_argumentos(ctx.param())

        etiquetas = self.labels.etiqueta_funcion(ctx.ID().getText())
        self.file.write(f'label {etiquetas[0]}\n')
        self.file.write(f'pop t0\n')

        for idx, arg in enumerate(args):
            tipo, nombre = arg
            self.file.write(f'pop {nombre}\n')
        self.inFuncion = 1
        self.visit(ctx.bloque())
        self.inFuncion = 0
        self.file.write(f'jmp t0\n')

    def visitBloque(self, ctx:compiladoresParser.BloqueContext):
        if ctx.instrucciones():
            self.visit(ctx.instrucciones())
        elif ctx.instruccion():
            self.visit(ctx.instruccion())

    def visitIelse(self, ctx: compiladoresParser.IelseContext):
        if ctx.instruccion():
            self.visit(ctx.instruccion())
        elif ctx.iif():
            self.visit(ctx.iif())

    def visitCond(self, ctx: compiladoresParser.CondContext):
        # La condición solo tiene un hijo: opal
        if ctx.opal():
            resultado = self.visit(ctx.opal())
            if resultado is not None:
                self.temporales.append(resultado)
            else:
                self.write("// ERROR: Condición no válida, no se generó temporal")
            return resultado
        # Si en el futuro agregas opcomp, opbool, etc., puedes agregarlos aquí:
        if ctx.opcomp():
            return self.visit(ctx.opcomp())
        if ctx.opbool():
            return self.visit(ctx.opbool())
        # Si no coincide ningún caso, devolver None
        return None
    
    def visitErrorNode(self, node):
        self.write(f"// ERROR: {node.getText()}")
        print(f"---- ERROR EN NODO: {node.getText()} ----")
        return super().visitErrorNode(node)
    
    def write(self, text):
        """Escribir con indentación apropiada"""
        if text.startswith('//'):
            self.file.write(text + '\n')
        else:
            self.file.write('    ' * self.indent_level + text + '\n')