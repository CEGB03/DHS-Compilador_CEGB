from compiladoresVisitor import compiladoresVisitor
from compiladoresParser import compiladoresParser
import os

class Temporales:
    def __init__(self):
        self.counter = 0
    def next_temporal(self):
        temporal = f't{self.counter}'
        self.counter += 1
        return temporal

class Etiquetas:
    def __init__(self):
        self.counter = 0
        self.funciones = dict()
    def next_etiqueta(self):
        etiqueta = f'l{self.counter}'
        self.counter += 1
        return etiqueta

    def etiqueta_funcion(self, identificador:str):
        # si el identificador existe, me devuelve la lista de etiquetas
        for id in self.funciones:
            if id == identificador:
                return self.funciones[id]
        # si el identificador no existe, debo generar las etiquetas para la funcion
        list = []
        etiqueta1 = self.next_etiqueta()
        etiqueta2 = self.next_etiqueta()
        list.append(etiqueta1)
        list.append(etiqueta2)
        self.funciones[identificador] = list
        return list

class Walker (compiladoresVisitor):
    temporales = []
    temps = Temporales()
    labels = Etiquetas()
    isFuncion = 0
    inFuncion = 0
    indent_level = 0
    
    def visitPrograma(self, ctx: compiladoresParser.ProgramaContext):
        # Verifica si hay errores antes de generar el código intermedio
        if os.path.exists("./output/Errores&Warnings.txt"):
            with open("./output/Errores&Warnings.txt") as errfile:
                if "ERROR" in errfile.read():
                    print("\033[1;31m"+"--- No se generó ningún código intermedio por errores ---"+"\033[0m")
                    return
        print("=-"*20)
        print("\033[1;32m"+"--- Generado codigo intermedio ---"+"\033[0m")
        self.f = open("./output/CodigoIntermedio.txt", "w")
        
        self.visit(ctx.instrucciones())
        self.f.close()
        
        # Verificar si el archivo tiene contenido
        with open("./output/CodigoIntermedio.txt", "r") as file:
            content = file.read()
            if content:
                print("\033[1;32m"+"--- Codigo intermedio generado ---"+"\033[0m")
            else:
                print("\033[1;31m"+"--- No se generó ningún código intermedio ---"+"\033[0m")
            
    def visitInstrucciones(self, ctx:compiladoresParser.InstruccionesContext):
        self.visit(ctx.instruccion())
        if ctx.instrucciones().getChildCount() != 0: # si hay mas de una intruccion
            self.visit(ctx.instrucciones())
        return
    
    def visitInstruccion(self, ctx:compiladoresParser.InstruccionContext):
        if ctx.declaracionPYC():
            self.visit(ctx.declaracionPYC())
        elif ctx.iwhile():  # Si es un bucle `while`
            self.visit(ctx.iwhile())
        elif ctx.ifor():  # Si es un bucle `for`
            self.visit(ctx.ifor())
        elif ctx.iif():  # Si es una estructura `if`
            self.visit(ctx.iif())
        elif ctx.asignacionPYC():  # Si es una asignación
            self.visit(ctx.asignacionPYC())
        elif ctx.protofun():
            self.visit(ctx.protofun())
        elif ctx.inic():
            self.visit(ctx.inic())
        elif ctx.returnfun():  # Si es una instrucción de retorno
            self.visit(ctx.returnfun())
        elif ctx.bloqueSolo():
            self.visit(ctx.bloqueSolo())
        elif ctx.deffuncion():  # Si es la definición de una función
            self.visit(ctx.deffuncion())
        elif ctx.llamadafun():
            self.visit(ctx.llamadafun())

    def visitDeclaracionPYC(self, ctx:compiladoresParser.DeclaracionPYCContext):
        self.visit(ctx.declaracion())
    
    def visitDeclaracion(self, ctx:compiladoresParser.DeclaracionContext):
        return super().visitDeclaracion(ctx)
        
    def visitInic(self, ctx:compiladoresParser.InicContext):
        if ctx.asignacionNum():
            self.visit(ctx.asignacionNum())
        elif ctx.asignacionBool():
            self.visit(ctx.asignacionBool())
        
    def visitLlamadafun(self, ctx:compiladoresParser.LlamadafunContext):
        return super().visitLlamadafun(ctx)
    
    def visitAsignacionPYC(self, ctx:compiladoresParser.AsignacionPYCContext):
        self.visit(ctx.asignacion())

    def visitBloqueSolo(self, ctx:compiladoresParser.BloqueSoloContext):
        self.visit(ctx.instrucciones())
    
    def visitAsignacion(self, ctx:compiladoresParser.AsignacionContext):
        if ctx.asignacionBool():
            self.visit(ctx.asignacionBool())
        elif ctx.asignacionNum():
            self.visit(ctx.asignacionNum())
    
    def visitAsignacionBool(self, ctx: compiladoresParser.AsignacionBoolContext):
        self.visit(ctx.opbool())  # Procesa la expresión booleana
        variable = ctx.ID().getText()  # Obtiene el identificador de la variable
        temporal = self.temporales.pop()  # Obtiene el temporal con el resultado
        self.f.write(f'{variable} = {temporal}\n')  # Genera la asignación en el código intermedio

    def visitOpbool(self, ctx: compiladoresParser.OpboolContext):
        self.visit(ctx.factorBool())
        izquierda = self.temporales.pop()
        if ctx.bools() is None:
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda}\n')  # Genera el código intermedio
            self.temporales.append(temporal)
        else:
            self.visit(ctx.bools())
            derecha = self.temporales.pop()
            operador = ctx.getChild(0).getChild(0).getText()  # Obtiene el operador lógico (&&, ||)
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)
        return self.temporales[-1]
        

                
    def visitBools(self, ctx:compiladoresParser.BoolsContext):
        # Si hay operador lógico (&&, ||, etc.)
        if ctx.getChildCount() == 3:
            # Estructura: opbool operador opbool
            self.visit(ctx.opbool(0))
            izquierda = self.temporales.pop()
            operador = ctx.getChild(1).getText()
            self.visit(ctx.opbool(1))
            derecha = self.temporales.pop()
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)
        else:
            # Caso base: solo un opbool, el temporal ya está en la pila
            self.visit(ctx.opbool(0))
            
            
    def visitFactorBool(self, ctx: compiladoresParser.FactorBoolContext):
        temporal = self.temps.next_temporal()
        if ctx.TRUE():
            self.f.write(f'{temporal} = 1\n')
        elif ctx.FALSE():
            self.f.write(f'{temporal} = 0\n')
        self.temporales.append(temporal)

    def visitAsignacionNum(self, ctx:compiladoresParser.AsignacionNumContext):
        # print("asigNum?? "+ctx.getText()) # esto entro sin que implemente asignacion...
        if self.inFuncion == 1:
            self.visit(ctx.exp())
            self.f.write(f'{ctx.ID().getText()} = {self.temporales.pop()}\n')
            return       
        # verificacion de llamado a funcion
        if ctx.exp().term().factor().funcionVar():
            self.isFuncion = 1
            self.visit(ctx.exp())
            self.f.write(f'pop {ctx.ID().getText()}\n')
        else:
            self.visit(ctx.exp())
            self.f.write(f'{ctx.ID().getText()} = {self.temporales[-1]}\n')
        return
    
    def visitExp(self, ctx:compiladoresParser.ExpContext):
        self.visit(ctx.term())
        if ctx.expPrima().getText() != "":
            self.visit(ctx.expPrima())
            derecha = self.temporales.pop()
            izquierda = self.temporales.pop()
            operador = ctx.expPrima().getChild(0).getText()
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)

    def visitExpPrima(self, ctx:compiladoresParser.ExpPrimaContext):
        if ctx.getChildCount() > 0:
            self.visit(ctx.exp())

    def visitTerm(self, ctx:compiladoresParser.TermContext):
        self.visit(ctx.factor())
        if ctx.t().getChildCount() != 0:
            self.visit(ctx.t())
            derecha = self.temporales.pop()
            izquierda = self.temporales.pop()
            operador = ctx.t().getChild(0).getText()
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)

    def visitT(self, ctx:compiladoresParser.TContext):
        if ctx.getChildCount() != 0:
            self.visit(ctx.factor())
            self.visit(ctx.t())
        
        return self.temporales[-1]

    
    def visitFactor(self, ctx:compiladoresParser.FactorContext):
        if ctx.PA():  # Si es una expresión entre paréntesis
            self.visit(ctx.exp())
        elif ctx.funcionVar():  # Si es una función o variable
            self.visit(ctx.funcionVar())
        else:  # Si es un valor literal
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {ctx.getText()}\n')
            self.temporales.append(temporal)
        
    def visitFuncionVar(self, ctx:compiladoresParser.FuncionVarContext):
        args = ctx.ids().getText().split(',')
        for arg in reversed([a.strip() for a in args if a.strip()]):
            self.f.write(f'push {arg}\n')
        etiquetas = self.labels.etiqueta_funcion(ctx.ID().getText())
        self.f.write(f'push {etiquetas[1]}\n')
        self.f.write(f'jmp {etiquetas[0]}\n')
        self.f.write(f'label {etiquetas[1]}\n')
        temp = self.temps.next_temporal()
        self.f.write(f'pop {temp}\n')
        self.temporales.append(temp)

    def visitDeffuncion(self, ctx:compiladoresParser.DeffuncionContext):
        etiquetas = self.labels.etiqueta_funcion(ctx.funcion().ID().getText())
        self.f.write(f'label {etiquetas[0]}\n')
        self.f.write(f'pop t0\n')  # dirección de retorno
    
        # Pop de argumentos en orden inverso
        args = []
        if ctx.funcion().argumentos():
            args = [arg.ID().getText() for arg in ctx.funcion().argumentos().argumento()]
            for arg in reversed(args):
                self.f.write(f'pop {arg}\n')
    
        # Cuerpo de la función
        self.inFuncion = 1
        self.visit(ctx.bloque())
        self.inFuncion = 0
    
        # El resultado debe estar en un temporal o variable, aquí se asume t1
        self.f.write(f'push t1\n')  # resultado
        self.f.write(f'jmp t0\n')
    
    def visitReturnfun(self, ctx:compiladoresParser.ReturnfunContext):
        if self.inFuncion == 1:
            if len(self.temporales) > 0:
                self.f.write(f'push {self.temporales.pop()}\n')
            else:
                self.visit(ctx.exp())
                self.f.write(f'push {self.temporales.pop()}\n')

    def visitBloque(self, ctx:compiladoresParser.BloqueContext):
        if ctx.instrucciones():  # Caso: Varias instrucciones
            self.visit(ctx.instrucciones())
        elif ctx.instruccion():  # Caso: Una sola instrucción
            self.visit(ctx.instruccion())
    
    def visitIif(self, ctx:compiladoresParser.IifContext):
        self.visit(ctx.cond())
        temp_cond = self.temporales.pop()
        etiqueta_else = self.labels.next_etiqueta()
        # Salto condicional
        self.write(f'ifnjmp {temp_cond}, {etiqueta_else}\n')
        etiqueta_fin = None
        self.indent_level += 1
        self.visit(ctx.bloque())
        self.indent_level -= 1
        if ctx.else_():
            etiqueta_fin = self.labels.next_etiqueta()
            self.write(f'jmp {etiqueta_fin}\n')
            self.f.write(f'label {etiqueta_else}\n')
            self.indent_level += 1
            self.visit(ctx.else_())
            self.indent_level -= 1
            self.f.write(f'label {etiqueta_fin}\n')
        else:
            self.f.write(f'label {etiqueta_else}\n')

    def visitElse(self, ctx:compiladoresParser.ElseContext):
        if ctx.bloque():
            self.visit(ctx.bloque())
        elif ctx.iif():
            self.visit(ctx.iif())
    
    def visitIwhile(self, ctx:compiladoresParser.IwhileContext):
        etiqueta_inicio = self.labels.next_etiqueta()
        etiqueta_fin = self.labels.next_etiqueta()
        self.f.write(f'label {etiqueta_inicio}\n')
        self.indent_level += 1
        self.visit(ctx.cond())
        temp_cond = self.temporales.pop()
        self.write(f'ifnjmp {temp_cond}, {etiqueta_fin}\n')
        self.visit(ctx.bloque())
        self.write(f'jmp {etiqueta_inicio}\n')
        self.indent_level -= 1
        self.f.write(f'label {etiqueta_fin}\n')
    
    def visitIfor(self, ctx: compiladoresParser.IforContext):
        etiqueta_inicio = self.labels.next_etiqueta()
        etiqueta_fin = self.labels.next_etiqueta()
        # Inicialización
        self.visit(ctx.init())
        # Escribe la etiqueta de inicio del ciclo
        self.f.write(f'label {etiqueta_inicio}\n')
        self.visit(ctx.cond())
        # Salta al final si la condición es falsa
        self.f.write(f'ifn {self.temporales.pop()} jmp {etiqueta_fin}\n')
        self.visit(ctx.bloque())
        # Incremento
        self.visit(ctx.iter())
        # Salta al inicio del ciclo para repetir
        self.f.write(f'jmp {etiqueta_inicio}\n')
        # Escribe la etiqueta del final del ciclo
        self.f.write(f'label {etiqueta_fin}\n')

    def visitCond(self, ctx):
        # Caso 1: Operación de comparación (opcomp)
        if ctx.opcomp():
            self.visit(ctx.opcomp())  # Visita la subregla opcomp
            return  # El resultado debe estar en el último temporal generado
        
        # Caso 2: Operación booleana (opbool)
        elif ctx.opbool():
            self.visit(ctx.opbool())  # Visita la subregla opbool
            return  # El resultado también debe estar en el último temporal generado 
        
    def visitOpcomp(self, ctx):
        left = ctx.ID().getText()  # Lado izquierdo (variable o identificador)
        operator = ctx.comps().getText()  # Operador de comparación (>, <, ==, etc.)
        right = ctx.factor().getText()  # Lado derecho (número, ID, etc.)
        
        # Generar un temporal para guardar el resultado de la comparación
        temp = self.temps.next_temporal()
        self.f.write(f"{temp} = {left} {operator} {right}\n")
        
        # Agregar el temporal a la pila
        self.temporales.append(temp)

    def visitOpbool(self, ctx: compiladoresParser.OpboolContext):
        if ctx.factorBool():
            self.visit(ctx.factorBool())
            # El temporal ya fue generado en visitFactorBool y está en la pila
        elif ctx.bools():
            self.visit(ctx.bools())
            # El temporal de la operación booleana está en la pila
        else:
            raise Exception("Error: Operación booleana inválida.")
    
    
    def visitErrorNode(self, node):
        print("---- ERROR ----")
        return super().visitErrorNode(node)
    
    def write(self, text):
        self.f.write('    ' * self.indent_level + text + '\n')