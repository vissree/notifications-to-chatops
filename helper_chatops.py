from helper_kms import KMSServiceClass
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json


def send_chat_notification(message, channel, hook_url, encrypted=True):
    """
    Send message to the channel using the given hook url.
    If hook_url is encrypted, the function expects the
    encrypted string to be base64 encoded. Returns the status and
    error message as a tuple of the below format. In case of success
    the error message is an empty string.
    (Boolean, String)
    """
    if encrypted:
        kms = KMSServiceClass()
        hook_url_plaintext = kms.decrypt(hook_url)
    else:
        hook_url_plaintext = hook_url

    slack_message = {
        "channel": channel,
        "text": message,
        "icon_emoji": ":fire_engine:",
    }

    req = Request(hook_url_plaintext, json.dumps(slack_message).encode("utf-8"))

    try:
        response = urlopen(req)
        response.read()
        status = True
        error = ""
    except (HTTPError, URLError) as e:
        status = False
        error = "Response Code {}: {}".format(e.code, e.reason)

    return (status, error)
