import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'error': 'Ha ocurrido un error, verifica los datos enviados'
        }
    else:
        logger.error(f"Error inesperado: {exc}", exc_info=True)
        response = Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response