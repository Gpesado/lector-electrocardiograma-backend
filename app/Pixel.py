class Pixel:
    def __init__(self, g, b, r):
        self.green = g
        self.blue = b
        self.red = r

    def mostrar(self):
        print(f"Green: {self.green}, Blue: {self.blue}, Red: {self.red}")