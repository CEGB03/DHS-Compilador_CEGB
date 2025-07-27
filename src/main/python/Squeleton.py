from abc import abstractmethod, ABC

class ID(ABC):
    #args = []
    @abstractmethod
    def __init__(self, nombre, tipoDato, inicializado=False, usado=False, declarado=True):
        self.nombre = nombre
        self.tipoDato = tipoDato
        self.inicializado = inicializado
        self.usado = usado
        self.declarado = declarado
    def get_tipoDato(self):
        return str(self.tipoDato)
    
    def set_inicializado(self):
        self.inicializado = True
    
    def set_usado(self):
        self.usado = True
    
    def __str__(self):
        return self.tipoDato+" "+self.nombre+": Inicializado? "+str(self.inicializado)+", Usado? "+str(self.usado)

class Variable(ID):
    def __init__(self, nombre, tipoDato, inicializado=False, usado=False, declarado=True):
        super().__init__(nombre, tipoDato, inicializado, usado, declarado)  
    def __str__(self):
        return "Variable: "+super().__str__()

class Funcion(ID):
    #args = []
    def __init__(self, nombre, tipoDato, inicializado=False, usado=False, declarado=True):
        super().__init__(nombre, tipoDato, inicializado, usado, declarado)
        self.prototipado = False
        self.args = []

    def set_args(self, args):
        self.args = args.copy() if args else []

    def set_usado(self):
        self.usado = True
    

    def __str__(self):
        prototipado = "Sí" if self.prototipado else "No"
        desarrollado = "Sí" if self.inicializado else "No"
        usado = "Sí" if self.usado else "No"
        return (f"Función: {self.tipoDato} {self.nombre}("
                f"args={self.args}) | Prototipado? {prototipado}, "
                f"Desarrollado? {desarrollado}, Usado? {usado}")
class Contexto:
    """
    Contexto son las anidaciones
    """
    ids = dict()
    nombreContexto=""
    def __init__(self, nombreContexto):
        # Diccionario con nombre como clave y la instancia de ID (Variable o Funcion) como valor
        self.ids = dict()
        self.nombreContexto = nombreContexto
        
    def agregarID(self, id):
        self.ids[id.nombre] = id 
        
    def __str__(self):
        # Crear una representación en cadena para todos los IDs en el contexto
        ids_repr = ""
        if self.ids == dict():
            ids_repr = "Sin contexto."
        else:
            for id in self.ids.values():
                ids_repr += id.__str__() + "\n"
        return "Contexto "+self.nombreContexto+": \n"+ ids_repr

class TablaSimbolos:
    """
    Dict<String, ID> tabla ==> es un diccionario porque el string 
                                osea el nombre del objeto será la referencia 
                                a la informacion guardada en el tipo ID
    """
    instancia = None
    contextos = []
    
    @staticmethod
    def get_instancia():
        """
        Crea la tabla si es que no existe previamente
        """
        if TablaSimbolos.instancia is None:
            TablaSimbolos.instancia = TablaSimbolos()
        return TablaSimbolos.instancia
        
    def __init__(self):
        if TablaSimbolos.instancia is not None:
            raise Exception("La clase Tabla de Simbolos no puede ser instanciada mas de una vez!")
        self.contextos = []
        self.contextos_historial = []  # <-- Agrega esto
        self.contextos.append(Contexto("Global"))
        TablaSimbolos.instancia = self

    def add_contexto(self, nombreContexto):
        nuevoContexto = Contexto(nombreContexto)
        self.contextos.append(nuevoContexto)
        self.contextos_historial.append(nuevoContexto)  # <-- Guarda el historial
        return nuevoContexto
        
    def del_Contexto(self):
        if self.contextos is not None and len(self.contextos) > 1:
            return self.contextos.pop()
        return None
        
    def add_identificador(self, id):
        """
        Agrega un identificador al contexto actual
        """
        self.contextos[-1].agregarID(id)
    
    def buscar_local(self, nombre):
        """
        Busca en el contexto actual (para for o funcion con argumentos)
        """
        contexto_actual = self.contextos[-1]
        #print(f"Buscando '{nombre}' en contexto: {contexto_actual.nombreContexto}, ids: {list(contexto_actual.ids.keys())}")
        return contexto_actual.ids.get(nombre)
            
    def buscar_global(self, nombre) -> ID:
        """
        Busca el contexto globalmente (para cosas anidadas)
        Incluye argumentos de función y variables en todos los contextos
        """
        # Buscar en todos los contextos, empezando por el más reciente
        for ctx in reversed(self.contextos):
            if nombre in ctx.ids:
                return ctx.ids[nombre]

        # Si no se encontró en contextos activos, buscar en historial
        for ctx in reversed(self.contextos_historial):
            if nombre in ctx.ids:
                return ctx.ids[nombre]

        return None
    def __str__(self):
        ctx_repr = ""
        for ctx in self.contextos_historial:
            ctx_repr += ctx.__str__() + "\n"
        return "Tabla de Simbolos:\n" + ctx_repr
    
    def mostrarVarsSinUsar(self):
        # Filtrar las variables y funciones desarrolladas que no han sido usadas
        vars_sin_usar = ""
        for contexto in self.contextos:
            for id in contexto.ids.values():
                # Solo reportar variables no usadas o funciones desarrolladas no usadas
                if not id.usado:
                    if isinstance(id, Funcion):
                        # Solo mostrar si está desarrollada (definida)
                        if not id.prototipado:
                            vars_sin_usar += id.__str__()+"\n"
                    else:
                        vars_sin_usar += id.__str__()+"\n"
        # Imprimir las variables sin usar
        if vars_sin_usar != "":
            print("Variables sin usar:")
            print(vars_sin_usar)
        else:
            print("No hay variables sin usar.")
    
    def reporte_variables_y_funciones_sin_usar(self):
        # Usar el historial de contextos
        for contexto in self.contextos_historial:
            vars_sin_usar = [id for id in contexto.ids.values()
                                if isinstance(id, Variable) and not id.usado]
            if contexto.nombreContexto.lower() != "global" and vars_sin_usar:
                print(f"Variables sin usar en función '{contexto.nombreContexto}':")
                for var in vars_sin_usar:
                    print("  " + str(var))
            elif contexto.nombreContexto.lower() == "global" and vars_sin_usar:
                print("Variables sin usar en contexto global:")
                for var in vars_sin_usar:
                    print("  " + str(var))
        # Reportar funciones desarrolladas no usadas
        funciones_no_usadas = []
        for contexto in self.contextos_historial:
            for id in contexto.ids.values():
                if isinstance(id, Funcion) and id.inicializado and not id.usado:
                    funciones_no_usadas.append(id)
        if funciones_no_usadas:
            print("Funciones desarrolladas pero no usadas:")
            for fun in funciones_no_usadas:
                print("  " + str(fun))
    
    def renombrar_contexto_actual(self, nombreContexto):
        """
        Cambia el nombre del contexto actual (el más reciente) por el nombre dado.
        """
        if self.contextos:
            contexto_actual = self.contextos[-1]
            contexto_actual.nombreContexto = nombreContexto
            
            # Buscar y actualizar también en el historial
            for i, ctx in enumerate(self.contextos_historial):
                if ctx is contexto_actual:
                    self.contextos_historial[i].nombreContexto = nombreContexto
                    break
    
    def marcar_main_como_usada(self, ignorar_main_usada=True):
        """
        Marca la función main como usada si la bandera está activa.
        """
        if ignorar_main_usada:
            for contexto in self.contextos_historial:
                for id in contexto.ids.values():
                    if isinstance(id, Funcion) and id.nombre == "main":
                        id.set_usado()
    
    def cargar_argumentos_en_contexto(self, funcion):
        """
        Dada una función con lista de argumentos (tipo, nombre),
        los agrega como Variables inicializadas al contexto actual.
        """
        for tipo, nombre in funcion.args:
            if nombre not in self.contextos[-1].ids:
                var_arg = Variable(nombre, tipo, inicializado=True, declarado=True)
                self.add_identificador(var_arg)