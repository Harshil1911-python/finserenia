"""
SERENIA ACCOUNTING — core/exceptions.py
==========================================
Custom DRF exception handler producing consistent error payloads
and ensuring no internal details (stack traces, secrets) leak to clients.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

logger = logging.getLogger('serenia.api')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # DRF already formatted the error — pass through as-is
        return response

    # Handle Django-level exceptions that DRF doesn't catch by default
    if isinstance(exc, DjangoValidationError):
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, IntegrityError):
        logger.warning("Integrity error: %s", exc)
        return Response(
            {'error': 'This operation conflicts with existing data (duplicate or referenced record).'},
            status=status.HTTP_409_CONFLICT,
        )

    # Catch-all — log full details server-side, return generic message to client
    logger.exception("Unhandled exception in API view", exc_info=exc)
    return Response(
        {'error': 'An unexpected error occurred. Please try again or contact support.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
