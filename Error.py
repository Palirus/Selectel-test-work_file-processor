class ReadFileException(Exception):
    def __init__(self, message: str = "Error reading file") -> None:
        self.message = message
        super().__init__(self.message)

class ParseFileException(Exception):
    def __init__(self, message: str = "Error parse file") -> None:
        self.message = message
        super().__init__(self.message)