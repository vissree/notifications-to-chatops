from botocore.exceptions import ClientError


def validate_client_conn(func):
    def func_wrapper(self, *args, **kwargs):
        if self.client:
            return func(self, *args, **kwargs)
        else:
            print("Client not initialized properly")
            return None

    return func_wrapper


def handle_client_errors(func):
    def func_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ClientError as e:
            print("Client error: {}".format(e))
            return None

    return func_wrapper
