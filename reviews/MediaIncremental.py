class MediaIncremental:
    def __init__(self):
        self.n = 0
        self.suma = 0

    def agregar(self, valor):
        self.n += 1
        self.suma += valor
        return self.media()

    def media(self):
        return self.suma / self.n if self.n > 0 else 0