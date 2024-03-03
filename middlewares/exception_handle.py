import logging
from django.http import JsonResponse
from utils.common_methods import logger


class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            if response.status_code >= 500:
                err = response.content[0:500]
                logger.log_error(f"Error ->  {str(err)}")
                response = JsonResponse({'detail': 'Internal Server Error'}, status=500)
            else:
                method = request.method
                path = request.path
                try:
                    user = (request.user and not request.user.is_anonymous) and request.user.user_id or 'Unknown user'
                except Exception as err:
                    user = 'Unknown user'
                log_message = f"INFO -> User Id {user} Accessed {method} :{path}."
                logger.log_info(log_message)
        except Exception as e:
            logger.log_error(f"Error -> Error on line {e.__traceback__.tb_lineno}, Error: {e}")
            response = JsonResponse({'detail': 'Internal Server Error'}, status=500)

        return response
