from antlr4 import ErrorNode, TerminalNode
from  compiladoresListener import compiladoresListener
from compiladoresParser import compiladoresParser
from Squeleton import *
import re
import inspect
# mientras se va creando el arbol, avanza
# para analisis semantico

class Escucha (compiladoresListener) :
    numTokens = 0 #tokens son las hojas
    numNodos = 0
    tabla = TablaSimbolos.get_instancia()
    def enterPrograma(self, ctx:compiladoresParser.ProgramaContext):
        print("\t\tComienza la compilacion")
        #print(self.tabla.__str__())

    # Exit a parse tree produced by compiladoresParser#programa.
    def exitPrograma(self, ctx:compiladoresParser.ProgramaContext):
        print("\t\tFin de la compilacion")
        # print("Se encontraron")
        # print("\tNodos: " + str(self.numNodos))
        # print("\tTokens: " + str(self.numTokens))
        print(self.tabla.__str__())
        self.tabla.mostrarVarsSinUsar()
        self.tabla.del_Contexto()
        
    
    def enterIwhile(self, ctx:compiladoresParser.IwhileContext):
        print("\t\tEnter WHILE")
        self.tabla.add_contexto("WHILE")
        
    def exitIwhile(self, ctx: compiladoresParser.IwhileContext):
        print(self.tabla.contextos[-1].__str__())
        print("\t\tFIN WHILE")
        
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\t" + ctx.getText())
        
        self.tabla.del_Contexto()
        
    def enterDeclaracion(self, ctx: compiladoresParser.DeclaracionContext):
        # print("\t\t Declaracion")
        pass
        
    def exitDeclaracion(self, ctx: compiladoresParser.DeclaracionContext):
        # se solucionadoria con if anidado y llamando al buscar por separado en cada caso
        nombreVariable = ctx.getChild(1).getText()
        tipoDeDato = ctx.getChild(0).getText()
        linea = ctx.start.line  
        
        variable = Variable(nombreVariable, tipoDeDato)
        
        #Las busquedas si devuelven None es porque encontraron algo
        busquedaGlobal = self.tabla.buscar_global(nombreVariable)
        busquedaLocal = self.tabla.buscar_local(nombreVariable)
        
        if busquedaLocal is None:
            if busquedaGlobal is None:
            #print('"'+nombreVariable+'"'+" no fue declarada previamente")
                self.tabla.add_identificador(variable)
                print("\033[1;32m" + f"Línea {linea}: La variable '{nombreVariable}' se declaró en el contexto actual." + "\033[0m")
            else:
                self.tabla.add_identificador(variable)
                print("\033[1;33m" + f"Línea {linea}: Advertencia: La variable '{nombreVariable}' es redeclarada en el contexto actual." + "\033[0m")
        else:
            print("\033[1;31m" + f"Línea {linea}: ERROR SEMÁNTICO: La variable '{nombreVariable}' fue declarada previamente en el contexto local." + "\033[0m")
            return
        
        
    def enterIfor(self, ctx: compiladoresParser.IforContext):
        print("\t\tEnter FOR")
        self.tabla.add_contexto("FOR")
        
    def exitIfor(self, ctx: compiladoresParser.IforContext):
        print(self.tabla.contextos[-1].__str__())
        print("\t\tFIN FOR")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\t" + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterIif(self, ctx: compiladoresParser.IifContext):
        print("\t\tENTER IF")
        self.tabla.add_contexto("IF")
    
    def exitIif(self, ctx: compiladoresParser.IifContext):
        print(self.tabla.contextos[-1].__str__())
        #print(ctx.IF.getText())
        print("\t\tEXIT IF")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\tTokens: " + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterElse(self, ctx: compiladoresParser.ElseContext):
        print("\t\tENTER ELSE")
        self.tabla.add_contexto("ELSE")
    
    def exitElse(self, ctx: compiladoresParser.ElseContext):
        print(self.tabla.contextos[-1].__str__())
        print("\t\tEXIT ELSE")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\tTokens: " + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterBloqueSolo(self, ctx:compiladoresParser.BloqueSoloContext):
        print("\t\tENTER BLOQUE")
        self.tabla.add_contexto("BLOQUE")
        
    def exitBloqueSolo(self, ctx: compiladoresParser.BloqueSoloContext):
        print(self.tabla.contextos[-1].__str__())
        print("\t\tEXIT BLOQUE")
        self.tabla.del_Contexto()

    def exitFuncionVar(self, ctx):
        nombreFuncion= ctx.getChild(0).getText().split('(')[0].strip() 
        #Guarde solo lo que estaba antes del parentesis porque sino guardaba todo el choclo y despues no coincidia
        linea = ctx.start.line
        args = ctx.getChild(2).getText().split(',')
        print(f"argumento:  {args}")
        busquedaGlobal = self.tabla.buscar_global(nombreFuncion)

        if busquedaGlobal is not None:
            for i in range(len(args)):
                busquedaGlobalArgs = self.tabla.buscar_global(args[i])
                if (busquedaGlobalArgs is not None and busquedaGlobalArgs.get_tipoDato() != busquedaGlobal.args[i]):
                    print("\033[1;31m"+ f"Línea {linea}: ERROR SEMANTICO: Los tipos de datos ("+ busquedaGlobalArgs.nombre+") ingresados no coinciden!"+ "\033[0m")
                    return
            if len(args) != len(busquedaGlobal.args):
                print("\033[1;31m"+ f"Línea {linea}: ERROR SEMANTICO: La cantidad de datos ingresados no coinciden!"+ "\033[0m")
                return
            else:#A CHEQUEAR
                busquedaGlobal.set_usado()
                            
        
    def enterProtofun(self, ctx: compiladoresParser.ProtofunContext):
        print("\t\tPROTOTIPO FUNCION")
        
    def exitProtofun(self, ctx: compiladoresParser.ProtofunContext):
        #Se agregan () para diferenciar de las variables y por si una funcion y una variable se llaman igual
        nombreFuncion= ctx.getChild(1).getText().split('(')[0].strip() #Guarde solo lo que estaba antes del parentesis porque sino guardaba todo el choclo y despues no coincidia
        linea = ctx.start.line
        if ctx.getChild(1).getChild(2) is not None:
            args = [re.match(r'^(int|float|double|bool|)+', tipo.strip()).group(0) for tipo in ctx.getChild(1).getChild(2).getText().split(',')]
        else:
            args=[]
        funcion = Funcion(nombreFuncion, ctx.getChild(0).getText())
        funcion.set_args(args) #guardo los argumentos en una lista ["int a", "int b"]
        print(f"Argumentos:  {funcion.args}")
        #print(funcion.args)    
        busquedaLocal = self.tabla.buscar_local(nombreFuncion)
        busquedaGlobal = self.tabla.buscar_global(nombreFuncion)
        if busquedaLocal is None and busquedaGlobal is None:
            print("\033[1;32m" + f"Línea {linea}: La función '{nombreFuncion}' se declaro en el contexto actual." + "\033[0m")
            funcion.set_inicializado()  # Marcar como inicializada
            self.tabla.add_identificador(funcion)
        elif busquedaLocal is not None:
            print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La función '{nombreFuncion}' ya está declarada en el contexto local." + "\033[0m")
        elif busquedaGlobal is not None:
            print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La función '{nombreFuncion}' ya está declarada en el contexto global." + "\033[0m")
        print("\t" + ctx.getText())
        
    def exitInic(self, ctx):
        nombreVariable = ctx.getChild(1).getText()
        linea = ctx.start.line  
        # Verificar que la declaración termine con ';'
        if not ctx.getText().endswith(";"):
            print("\033[1;31m" + f"Línea {linea}: ERROR SINTACTICO: La declaración debe terminar con ';'." + "\033[0m")
            return
        
        # Si el nombre de la variable contiene un '=', extraemos solo el nombre
        if '=' in nombreVariable:
            nombreVariable = nombreVariable.split('=')[0].strip()

        # Chequear si existe en el contexto actual o global
        busquedaLocal = self.tabla.buscar_local(nombreVariable)
        busquedaGlobal = self.tabla.buscar_global(nombreVariable)
        tipoDeDato = ctx.getChild(0).getText()
        variable = Variable(nombreVariable, tipoDeDato)

        # Si la variable no existe en ningún contexto, la inicializamos y agregamos
        if busquedaLocal is None and busquedaGlobal is None:
            print("\033[1;32m" + f"Línea {linea}: La variable '{nombreVariable}' se inicializó en el contexto actual." + "\033[0m")
            variable.set_inicializado()  # Marcar como inicializada
            self.tabla.add_identificador(variable)
        elif busquedaLocal is not None:
            print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariable}' ya está declarada en el contexto local." + "\033[0m")
        elif busquedaGlobal is not None:
            print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariable}' ya está declarada en el contexto global." + "\033[0m")

    def exitAsignacion(self, ctx):
        operacion = ctx.getChild(0).getText()
        linea = ctx.start.line  
        # Verificar si el nombre de la variable de la izquierda contiene un '='
        if '=' in operacion:
            nombreVariableIzquierda = operacion.split('=')[0].strip()
            expresionDerecha = operacion.split('=')[1].strip()
            
            busquedaLocalIzquierda = self.tabla.buscar_local(nombreVariableIzquierda)
            busquedaGlobalIzquierda = self.tabla.buscar_global(nombreVariableIzquierda)

            # Asegurarse de que la variable izquierda está declarada
            if busquedaLocalIzquierda is None and busquedaGlobalIzquierda is None:
                print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariableIzquierda}' no fue declarada previamente." + "\033[0m")
                return
            
            # Obtener el tipo de la variable izquierda
            tipoIzquierda = (busquedaLocalIzquierda.tipoDato if busquedaLocalIzquierda else busquedaGlobalIzquierda.tipoDato)

            # Procesar la expresión de la derecha, ignorando operadores aritméticos
            terminos = re.split(r'(\+|-|\*|/)', expresionDerecha)
            
            for termino in terminos:
                termino = termino.strip()
                if termino in {'+', '-', '*', '/'}:
                    # Ignorar operadores aritméticos
                    continue
                elif termino.isdigit():
                    # Si es un número, continuar
                    continue
                elif termino.isidentifier() or (re.search(r'[()]', termino)):  # Verificar si es un identificador (variable) o una funcion
                    
                    if(re.search(r'[()]', termino)): 
                        termino= re.sub(r'\(.*?\)', '', termino) #Si es una funcion le quita los parentesis y el contenido
                    # Buscar la variable en el contexto
                    busquedaLocalDerecha = self.tabla.buscar_local(termino)
                    busquedaGlobalDerecha = self.tabla.buscar_global(termino)

                    # Verificar que la variable esté declarada
                    if busquedaLocalDerecha is None and busquedaGlobalDerecha is None:
                        print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{termino}' no fue declarada previamente." + "\033[0m")
                        return

                    # Obtener el tipo de la variable derecha
                    tipoDerecha = (busquedaLocalDerecha.tipoDato if busquedaLocalDerecha else busquedaGlobalDerecha.tipoDato)

                    # Verificar compatibilidad de tipos
                    if tipoIzquierda != tipoDerecha:
                        print("\033[1;33m" + f"Línea {linea}: Advertencia: No se puede asignar un valor de tipo '{tipoDerecha}' a una variable de tipo '{tipoIzquierda}'." + "\033[0m")
                        return
                    
                    # Marcar la variable como usada
                    if busquedaLocalDerecha:
                        busquedaLocalDerecha.set_usado()
                    else:
                        busquedaGlobalDerecha.set_usado()
                else:
                    # Error si no es un número ni una variable válida
                    print("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: El término '{termino}' no es válido en la expresión de asignación." + "\033[0m")
                    return

            # Si todos los términos son válidos, proceder con la asignación
            print("\033[1;32m" + f"Línea {linea}: Asignación válida: '{nombreVariableIzquierda}' = '{expresionDerecha}'." + "\033[0m")
            
            # Marcar la variable izquierda como usada
            if busquedaLocalIzquierda is not None:
                busquedaLocalIzquierda.set_usado()
            else:
                busquedaGlobalIzquierda.set_usado()

    def enterDeffuncion(self, ctx:compiladoresParser.DeffuncionContext):
        print("\t\tENTER FUNCION")
        self.tabla.add_contexto("FUNCION")
    
    def exitDeffuncion(self, ctx:compiladoresParser.DeffuncionContext):
        print(self.tabla.contextos[-1].__str__())
        print("\t\tEXIT FUNCION")
        self.tabla.del_Contexto()
        
    def visitTerminal(self, node: TerminalNode):
        # print(" ---> Token: " + node.getText())
        self.numTokens += 1
        
    def visitErrorNode(self, node: ErrorNode):
        print("\033[1;31m" +" ERROR SINTACTICO"+ "\033[0m")
        print(node.getText())
        
    def enterEveryRule(self, ctx):
        self.numNodos += 1
        