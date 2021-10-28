# Excepciones personalizadas
class Error(Exception):

    def __init__(self, message="Error en tiempo de ejecución"):
        self.message = f"Error: {message}"
        super().__init__(self.message)

class ErrorConfiguracionGeneralNoDefinida(Error):
    
    def __init__(self, message="No se ha definido la configuracion general del sistema"):
        self.message = message
        super().__init__(self.message)

