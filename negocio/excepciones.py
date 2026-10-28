"""Errores de negocio que la capa de presentación muestra al usuario."""


class ErrorNegocio(Exception):
    """Error esperado: datos inválidos o una operación no permitida."""


class SinConclusionError(ErrorNegocio):
    """Ninguna regla de inferencia se cumple con los hechos dados."""


class CredencialesInvalidasError(ErrorNegocio):
    pass
