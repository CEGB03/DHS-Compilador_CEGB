from compiladoresVisitor import compiladoresVisitor
from compiladoresParser import compiladoresParser
# para crear codigo intermedio

class Walker (compiladoresVisitor):
    def visitPrograma(self, ctx: compiladoresParser):
        print("=-"*20) # hace esto 20 veces
        print("--- Comienza a caminar ---")
        tmp = super().visitPrograma(ctx) # (para enganchar el recorrido normal) para no visitar nada pongo tmp = None
        print("--- Fin de recorrido ---")
        return tmp
    def visitBloque(self, ctx: compiladoresParser):
        print("--- Nuevo contexto ---")
        print(ctx.getText())
        return super().visitBloque(ctx)
        #return super().visitDeclaracion(ctx.getChild(1)) # omite imprimir las llaves de la anidacion
    def visitTerminal(self, node):
        print("==> Token " + node.getText())
        return super().visitTerminal(node)
    def visitDeclaracion(self, ctx): # devuelve el tipo de variable seguido de su id
        print(ctx.getChild(0).getText()+
              " - " + 
              ctx.getChild(1). getText())
        #return super().visitDeclaracion(ctx)
        return None
    def visitIwhile(self, ctx):
        print("---- WHILE ----")
        return super().visitIwhile(ctx)
    def visitIfor(self, ctx):
        print("---- FOR ----")
        return super().visitIfor(ctx)
    def visitErrorNode(self, node):
        print("---- ERROR ----")
        return super().visitErrorNode(node)