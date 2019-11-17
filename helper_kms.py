from helper_decorators import handle_client_errors, validate_client_conn
from helper_core import ServiceClass
from base64 import b64decode


class KMSServiceClass(ServiceClass):
    def __init__(self):
        super().__init__("kms")

    @handle_client_errors
    @validate_client_conn
    def decrypt(self, encrypted_string, base64_encoded=True):
        """
        Decrypts the given cipher text. By defaults expects a
        base64 encoded string.
        """
        if base64_encoded:
            cipher_text_blob = b64decode(encrypted_string)
        else:
            cipher_text_blob = encrypted_string

        return self.client.decrypt(CiphertextBlob=cipher_text_blob)["Plaintext"].decode(
            "utf-8"
        )
