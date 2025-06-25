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
    error = False
    indent_level = 0

    def __init__(self):
        self.compilacion_file = open('./output/Compilacion.txt', 'w')

    def write(self, text):
        self.compilacion_file.write('    ' * self.indent_level + text + '\n')

    def write_centered(self, text, width=50):
        text = f" {text} "
        guiones = width - len(text)
        left = guiones // 2
        right = guiones - left
        self.compilacion_file.write('-' * left + text + '-' * right + '\n')

    def enterPrograma(self, ctx:compiladoresParser.ProgramaContext):
        self.write_centered("Comienza la compilacion")

    # Exit a parse tree produced by compiladoresParser#programa.
    def exitPrograma(self, ctx:compiladoresParser.ProgramaContext):
        self.write_centered("Fin de la compilacion")
        # Escribir tabla de símbolos en el archivo de compilación
        self.compilacion_file.write("\n--- Variables y funciones declaradas ---\n")
        for contexto in self.tabla.contextos:
            self.compilacion_file.write(f"Contexto {contexto.nombreContexto}:\n")
            for id in contexto.ids.values():
                self.compilacion_file.write(f"    {id}\n")
        self.compilacion_file.close()
        # Tabla de símbolos y variables sin usar solo por consola
        print(self.tabla.__str__())
        self.tabla.mostrarVarsSinUsar()
        self.tabla.del_Contexto()

    def enterIwhile(self, ctx:compiladoresParser.IwhileContext):
        self.write("Enter WHILE")
        self.indent_level += 1
        self.tabla.add_contexto("WHILE")

    def exitIwhile(self, ctx: compiladoresParser.IwhileContext):
        self.indent_level -= 1
        self.write("FIN WHILE")
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
                self.write(f"Declarada {variable} en línea {linea}")
                print("\033[1;32m" + f"Línea {linea}: La variable '{nombreVariable}' se declaró en el contexto actual." + "\033[0m")
            else:
                self.tabla.add_identificador(variable)
                self.write(f"Advertencia: redeclarada {variable} en línea {linea}")
                print("\033[1;33m" + f"Línea {linea}: Advertencia: La variable '{nombreVariable}' es redeclarada en el contexto actual." + "\033[0m")
        else:
            self.log_error("\033[1;31m" + f"Línea {linea}: ERROR SEMÁNTICO: La variable '{nombreVariable}' fue declarada previamente en el contexto local." + "\033[0m")
            self.error = True
            return
        
        
    def enterIfor(self, ctx: compiladoresParser.IforContext):
        self.write("Enter FOR")
        self.indent_level += 1
        self.tabla.add_contexto("FOR")
        
    def exitIfor(self, ctx: compiladoresParser.IforContext):
        self.indent_level -= 1
        self.write("FIN FOR")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\t" + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterIif(self, ctx: compiladoresParser.IifContext):
        self.write("ENTER IF")
        self.indent_level += 1
        self.tabla.add_contexto("IF")
    
    def exitIif(self, ctx: compiladoresParser.IifContext):
        self.indent_level -= 1
        self.write("EXIT IF")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\tTokens: " + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterElse(self, ctx: compiladoresParser.ElseContext):
        self.write("ENTER ELSE")
        self.indent_level += 1
        self.tabla.add_contexto("ELSE")
    
    def exitElse(self, ctx: compiladoresParser.ElseContext):
        self.indent_level -= 1
        self.write("EXIT ELSE")
        # print("\tCantidad de hijos: " + str(ctx.getChildCount()))
        # print("\tTokens: " + ctx.getText())
        self.tabla.del_Contexto()
        
    def enterBloqueSolo(self, ctx:compiladoresParser.BloqueSoloContext):
        self.write("ENTER BLOQUE")
        self.indent_level += 1
        self.tabla.add_contexto("BLOQUE")
        
    def exitBloqueSolo(self, ctx: compiladoresParser.BloqueSoloContext):
        self.indent_level -= 1
        self.write("EXIT BLOQUE")
        self.tabla.del_Contexto()

    def exitFuncionVar(self, ctx):
        nombreFuncion = ctx.getChild(0).getText().split('(')[0].strip() 

        linea = ctx.start.line
        args = ctx.getChild(2).getText().split(',')
        busquedaGlobal = self.tabla.buscar_global(nombreFuncion)

        # Marcar variables usadas como argumentos
        for arg in args:
            arg = arg.strip()
            if arg.isidentifier():
                var_local = self.tabla.buscar_local(arg)
                var_global = self.tabla.buscar_global(arg)
                if var_local:
                    var_local.set_usado()
                elif var_global:
                    var_global.set_usado()

        if busquedaGlobal is not None:
            for i in range(len(args)):
                busquedaGlobalArgs = self.tabla.buscar_global(args[i])
                if (busquedaGlobalArgs is not None and busquedaGlobalArgs.get_tipoDato() != busquedaGlobal.args[i]):
                    self.log_error("\033[1;31m"+ f"Línea {linea}: ERROR SEMANTICO: Los tipos de datos ("+ busquedaGlobalArgs.nombre+") ingresados no coinciden!"+ "\033[0m")
                    self.error = True
                    return
            if len(args) != len(busquedaGlobal.args):
                self.log_error("\033[1;31m"+ f"Línea {linea}: ERROR SEMANTICO: La cantidad de datos ingresados no coinciden!"+ "\033[0m")
                self.error = True
                return
    # no la marcamos como usada porque se encarga la asignacion
                            
        
    def exitProtofun(self, ctx: compiladoresParser.ProtofunContext):
        nombreFuncion = ctx.getChild(1).getText().split('(')[0].strip()
        linea = ctx.start.line
        if ctx.getChild(1).getChild(2) is not None:
            args = [re.match(r'^(int|float|double|bool|)+', tipo.strip()).group(0) for tipo in ctx.getChild(1).getChild(2).getText().split(',')]
        else:
            args = []
        funcion = Funcion(nombreFuncion, ctx.getChild(0).getText())
        funcion.set_args(args)
        funcion.prototipado = True  # Marca como prototipado
        busquedaLocal = self.tabla.buscar_local(nombreFuncion)
        busquedaGlobal = self.tabla.buscar_global(nombreFuncion)
        if busquedaLocal is None and busquedaGlobal is None:
            self.write(f"Declarada Función: {funcion.tipoDato} {nombreFuncion}: Prototipado? True en línea {linea}")
            print("\033[1;32m" + f"Línea {linea}: La función '{nombreFuncion}' se declaró en el contexto actual." + "\033[0m")
            self.tabla.add_identificador(funcion)
        else:
            self.write(f"Advertencia: redeclarada función {funcion.tipoDato} {nombreFuncion}: Prototipado? True en línea {linea}")
            print("\033[1;33m" + f"Línea {linea}: Advertencia: La función '{nombreFuncion}' es redeclarada en el contexto actual." + "\033[0m")
        
    def exitInic(self, ctx):
        nombreVariable = ctx.getChild(1).getText()
        linea = ctx.start.line  
        tipoDeDato = ctx.getChild(0).getText()
        # Verificar que la declaración termine con ';'
        if not ctx.getText().endswith(";"):
            self.log_error("\033[1;31m" + f"Línea {linea}: ERROR SINTACTICO: La declaración debe terminar con ';'." + "\033[0m")
            self.error = True
            return
        if '=' in nombreVariable:
            nombreVariable = nombreVariable.split('=')[0].strip()
        busquedaLocal = self.tabla.buscar_local(nombreVariable)
        busquedaGlobal = self.tabla.buscar_global(nombreVariable)
        variable = Variable(nombreVariable, tipoDeDato)
        if busquedaLocal is None and busquedaGlobal is None:
            variable.set_inicializado()
            self.tabla.add_identificador(variable)
            self.write(f"Declarada Variable: {tipoDeDato} {nombreVariable}: Inicializado? True, Usado? False en línea {linea}")
            print("\033[1;32m" + f"Línea {linea}: La variable '{nombreVariable}' se declaró en el contexto actual." + "\033[0m")
        elif busquedaLocal is not None:
            self.log_error("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariable}' ya está declarada en el contexto local." + "\033[0m")
            self.error = True
        elif busquedaGlobal is not None:
            self.log_error("\033[1;31m" + f"Línea {linea}: ERROR SEMANTICO: La variable '{nombreVariable}' ya está declarada en el contexto global." + "\033[0m")
            self.error = True

    def exitAsignacion(self, ctx):
        operacion = ctx.getChild(0).getText()
        linea = ctx.start.line  
        if '=' in operacion:
            nombreVariableIzquierda = operacion.split('=')[0].strip()
            expresionDerecha = operacion.split('=')[1].strip()
            busquedaLocalIzquierda = self.tabla.buscar_local(nombreVariableIzquierda)
            busquedaGlobalIzquierda = self.tabla.buscar_global(nombreVariableIzquierda)
            variable = busquedaLocalIzquierda or busquedaGlobalIzquierda
            if variable is None:
                self.log_error(f"ERROR: Variable no declarada: {nombreVariableIzquierda} en línea {linea}")
                return

            # Validación de tipo: no permitir asignar booleanos a enteros, ni viceversa
            tipoIzquierda = variable.tipoDato
            if (("TRUE" in expresionDerecha or "FALSE" in expresionDerecha) and tipoIzquierda != "bool"):
                self.log_error(f"\033[1;31mLínea {linea}: ERROR SEMANTICO: No se puede asignar un booleano a una variable de tipo {tipoIzquierda}.\033[0m")
                self.error = True
                return
            if tipoIzquierda == "bool" and re.search(r'\b\d+\b', expresionDerecha):
                self.log_error(f"\033[1;31mLínea {linea}: ERROR SEMANTICO: No se puede asignar un valor numérico a una variable booleana.\033[0m")
                self.error = True
                return

            # Marcar variables usadas en la expresión derecha
            for token in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expresionDerecha):
                if token != nombreVariableIzquierda:
                    self.marcar_variable_usada(token, linea)
            variable.set_inicializado()
            self.write(f"Modificada Variable: {variable.tipoDato} {nombreVariableIzquierda}: Inicializado? {variable.inicializado}, Usado? {variable.usado} en línea {linea}")
            print("\033[1;32m" + f"Línea {linea}: La variable '{nombreVariableIzquierda}' fue modificada en el contexto actual." + "\033[0m")
        
    def enterDeffuncion(self, ctx: compiladoresParser.DeffuncionContext):
        self.write("ENTER FUNCION")
        self.indent_level += 1
        self.tabla.add_contexto("FUNCION")
        # Marcar si la función ya fue prototipada
        nombreFuncion = ctx.getChild(1).getText().split('(')[0].strip()
        busquedaGlobal = self.tabla.buscar_global(nombreFuncion)
        if busquedaGlobal is not None and hasattr(busquedaGlobal, 'prototipado') and busquedaGlobal.prototipado:
            self.write(f"Definida Función: {busquedaGlobal.tipoDato} {nombreFuncion}: Prototipado? True")
        else:
            tipoDato = ctx.getChild(0).getText()
            self.write(f"Definida Función: {tipoDato} {nombreFuncion}: Prototipado? False")
    
    def exitDeffuncion(self, ctx:compiladoresParser.DeffuncionContext):
        self.indent_level -= 1
        self.write("EXIT FUNCION")
        self.tabla.del_Contexto()
        
    def visitTerminal(self, node: TerminalNode):
        # print(" ---> Token: " + node.getText())
        self.numTokens += 1
        
    def visitErrorNode(self, node: ErrorNode):
        mensaje = "\033[1;31m ERROR SINTACTICO\033[0m\n" + node.getText()
        self.log_error(mensaje)
        self.error = True
        
    def enterEveryRule(self, ctx):
        self.numNodos += 1
    
    def marcar_variable_usada(self, nombre, linea):
        var_local = self.tabla.buscar_local(nombre)
        var_global = self.tabla.buscar_global(nombre)
        if var_local:
            if isinstance(var_local, Funcion):
                var_local.set_usado()
                self.write(f"Usada Función: {var_local.tipoDato} {nombre}: Prototipado? {getattr(var_local, 'prototipado', False)}, Usado? {var_local.usado} en línea {linea}")
                print("\033[1;32m" + f"Línea {linea}: La función '{nombre}' fue usada en el contexto actual." + "\033[0m")
            else:
                var_local.set_usado()
                self.write(f"Usada Variable: {var_local.tipoDato} {nombre}: Inicializado? {var_local.inicializado}, Usado? {var_local.usado} en línea {linea}")
                print("\033[1;32m" + f"Línea {linea}: La variable '{nombre}' fue usada en el contexto actual." + "\033[0m")
        elif var_global:
            if isinstance(var_global, Funcion):
                var_global.set_usado()
                self.write(f"Usada Función: {var_global.tipoDato} {nombre}: Prototipado? {getattr(var_global, 'prototipado', False)}, Usado? {var_global.usado} en línea {linea}")
                print("\033[1;32m" + f"Línea {linea}: La función '{nombre}' fue usada en el contexto global." + "\033[0m")
            else:
                var_global.set_usado()
                self.write(f"Usada Variable: {var_global.tipoDato} {nombre}: Inicializado? {var_global.inicializado}, Usado? {var_global.usado} en línea {linea}")
                print("\033[1;32m" + f"Línea {linea}: La variable '{nombre}' fue usada en el contexto global." + "\033[0m")
    
    def log_error(self, mensaje):
        # Escribe en consola
        print(mensaje)
        # Escribe en el archivo de errores
        with open('./output/Errores&Warnings.txt', 'a', encoding='utf-8') as f:
            f.write(mensaje + '\n')