from abc import abstractmethod, ABC

class ID(ABC):
    args = []
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
        return "ID: "+self.tipoDato+" "+self.nombre+": Inicializado? "+str(self.inicializado)+", Usado? "+str(self.usado)

class Variable(ID):
    def __init__(self, nombre, tipoDato, inicializado=False, usado=False, declarado=True):
        super().__init__(nombre, tipoDato, inicializado, usado, declarado)  

class Funcion(ID):
    args = []
    def __init__(self, nombre, tipoDato, inicializado=False, usado=False, declarado=True):
        super().__init__(nombre, tipoDato, inicializado, usado, declarado)

    def set_args(self, args):
        self.args = args  
          
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
        self.contextos.append(Contexto("Global"))
        TablaSimbolos.instancia = self
        
    def add_contexto(self, nombreContexto):
        """
        Agrega un nuevo contexto a la tabla de simbolos
        """
        print("Agregando contexto ......")
        #print("Instancia: "+ self.get_instancia().getText())
        nuevoContexto = Contexto(nombreContexto)
        self.contextos.append(nuevoContexto)
        return nuevoContexto
        
    def del_Contexto(self):
        """
        Elimina el ultimo contexto
        """
        #print(self.__str__())
        if self.contextos is not None:
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
        return contexto_actual.ids.get(nombre)
            
    def buscar_global(self, nombre) -> ID:
        """
        Busca el contexto globalmente (para cosas anidadas)
        """
        for ctx in reversed(self.contextos):
            if nombre in ctx.ids:
                return ctx.ids[nombre]
        return None
    def __str__(self):
        ctx_repr = ""
        for ctx in self.contextos:
            ctx_repr += ctx.__str__() + "\n"
        return "Tabla de Simbolos:\n" + ctx_repr
    
    def mostrarVarsSinUsar(self):
        # Filtrar las variables que no han sido usadas
        vars_sin_usar = ""
        for contexto in self.contextos:
            for id in contexto.ids.values():
                if not id.usado:  # Verificar si la variable no ha sido usada
                    vars_sin_usar += id.__str__()+"\n"
        
        # Imprimir las variables sin usar
        if vars_sin_usar != "":
            print("Variables sin usar:")
            # for id in vars_sin_usar:
            #     print(id)  # Esto llamará al método _str_ de la clase ID
            print(vars_sin_usar)
        else:
            print("No hay variables sin usar.")