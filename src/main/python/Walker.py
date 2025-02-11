from compiladoresVisitor import compiladoresVisitor
from compiladoresParser import compiladoresParser

class Temporales:
    def __init__(self):
        self.counter = 0
    def next_temporal(self):
        temporal = f'temp{self.counter}'
        self.counter += 1
        return temporal

class Etiquetas:
    funciones = dict()
    counter = 0

    def next_etiqueta(self):
        etiqueta = f'label{self.counter}'
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
    
    def visitPrograma(self, ctx: compiladoresParser.ProgramaContext):
        print("=-"*20) # hace esto 20 veces
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
        if ctx.getChild(0) is not None:
            operador = ctx.getChild(0).getText()
            self.visit(ctx.opbool())
            derecha = self.temporales.pop()
            izquierda = self.temporales.pop()
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)
            
        return self.temporales[-1]
            
            
            
    def visitFactorBool(self, ctx: compiladoresParser.FactorBoolContext):
        if ctx.TRUE():  # Si es `true`
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = 1\n')  # Asigna 1 como verdadero
            self.temporales.append(temporal)
        elif ctx.FALSE():  # Si es `false`
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = 0\n')  # Asigna 0 como falso
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
            temporal = self.temps.next_temporal()
            self.temporales.append(temporal)
            derecha = self.temporales.pop()
            if ctx.expPrima().getChild(1) is not None:
                operador = ctx.expPrima().getChild(0).getText()  # Obtiene el operador
                self.visit(ctx.expPrima())  # Visita el resto de la expresión
                self.f.write(f'{temporal} = {derecha} {operador} {self.temporales.pop()}\n')
                return
            else:
                self.f.write(f'{temporal} = {derecha}\n')
    
    def visitExpPrima(self, ctx:compiladoresParser.ExpPrimaContext):
        if ctx.getChild(0) is not None:
            operador = ctx.getChild(0).getText()
            self.visit(ctx.exp())
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {self.temporales.pop()} {operador} {self.temporales.pop()}\n')
            self.temporales.append(temporal)
    
    def visitTerm(self, ctx:compiladoresParser.TermContext):
        self.visit(ctx.factor())  # Visita el factor inicial
        if ctx.t().getChildCount() != 0:  # Si hay más términos
            operador = ctx.getChild(1).getText()
            self.visit(ctx.t())
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {self.temporales.pop()} {operador} {self.temporales.pop()}\n')
            self.temporales.append(temporal)
    
    def visitT(self, ctx:compiladoresParser.TContext):
        if ctx.getChildCount() != 0:
            operador = ctx.getChild(0).getText()
            self.visit(ctx.factor())
            derecha = self.temporales.pop()
            izquierda = self.temporales.pop()
            temporal = self.temps.next_temporal()
            self.f.write(f'{temporal} = {izquierda} {operador} {derecha}\n')
            self.temporales.append(temporal)
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
        self.visit(ctx.ids())  # Visita los argumentos de la función
        etiquetas = self.labels.etiqueta_funcion(ctx.ID().getText())  # Genera etiquetas
        self.f.write(f'push {etiquetas[1]}\n')
        self.f.write(f'jmp {etiquetas[0]}\n')
        self.f.write(f'label {etiquetas[1]}\n')
        self.isFuncion = 0
    
    def visitDeffuncion(self, ctx:compiladoresParser.DeffuncionContext):
        if ctx.ID().getText() != 'main':  # Si no es la función principal
            self.inFuncion = 1
            etiquetas = self.labels.etiqueta_funcion(ctx.funcion().ID().getText())
            self.f.write(f'label {etiquetas[0]}\n')

            if ctx.funcion().argumentos():  # Si hay argumentos
                self.visit(ctx.argumentos())

            self.f.write(f'pop {etiquetas[1]}\n')
            self.visit(ctx.instrucciones())
            self.f.write(f'jmp {etiquetas[1]}\n')
            self.inFuncion = 0
        else:  # Si es la función principal
            self.visit(ctx.instrucciones())
    
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
        self.visit(ctx.cond())  # Visita la condición
        etiqueta_else = self.labels.next_etiqueta()
        
        # Genera el salto condicional al bloque else (si existe)
        self.f.write(f'ifn {self.temporales.pop()} jmp {etiqueta_else}\n')
        self.visit(ctx.bloque())  # Visita el bloque del `if`

        if ctx.else_():
            etiqueta_fin = self.labels.next_etiqueta()
            self.f.write(f'jmp {etiqueta_fin}\n')
            self.f.write(f'label {etiqueta_else}\n')
            self.visit(ctx.else_())  # Visita el bloque del `else`
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

        # Escribe la etiqueta de inicio del ciclo
        self.f.write(f'label {etiqueta_inicio}\n')
        self.visit(ctx.cond())  # Visita la condición

        # Salta al final si la condición es falsa
        self.f.write(f'ifn {self.temporales.pop()} jmp {etiqueta_fin}\n')
        self.visit(ctx.bloque())  # Visita el bloque del `while`

        # Salta al inicio del ciclo para repetir
        self.f.write(f'jmp {etiqueta_inicio}\n')

        # Escribe la etiqueta del final del ciclo
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

    def visitOpbool(self, ctx):
        if ctx.factorBool():  # Es un valor booleano simple (TRUE/FALSE)
            bool_value = ctx.factorBool().getText()
            temp = self.temps.next_temporal()
            self.f.write(f"{temp} = {bool_value}\n")
            self.temporales.append(temp)
        elif ctx.bools():  # Es una operación booleana (AND, OR)
            self.visit(ctx.bools())
        else:
            raise Exception("Error: Operación booleana inválida.")

    
    
    def visitErrorNode(self, node):
        print("---- ERROR ----")
        return super().visitErrorNode(node)