from sentry_sdk import capture_exception, configure_scope


def log_error(base_error, message):
    with configure_scope() as scope:
        scope.set_extra('base_error', base_error)
        capture_exception(message)


def log_request_error(response, message, extra=None):
    with configure_scope() as scope:
        if extra:
            for k in extra:
                scope.set_extra(k, extra[k])
        scope.set_extra('req_error', response.reason)
        capture_exception(message)
