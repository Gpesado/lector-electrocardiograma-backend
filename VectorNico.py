class VectorNico:
    def __init__(self, tiempo, valor):
        self.tiempo = tiempo
        self.valor = valor

    def mostrar(self):
        print(f"Tiempo: {self.tiempo}, Valor: {self.valor}")
        
    def toString(self):
        return (f"Tiempo: {self.tiempo}, Valor: {self.valor}")