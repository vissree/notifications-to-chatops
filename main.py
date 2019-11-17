from helper_chatops import send_chat_notification
import json
import logging
import os

"""
Follow these steps to configure the webhook in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Incoming WebHooks".

  3. Choose the default channel where messages will be sent and click "Add Incoming WebHooks Integration".

  4. Copy the webhook URL from the setup instructions and use it in the next section.

To encrypt your secrets use the following steps:

  1. Create or use an existing KMS Key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html

  2. Click the "Enable Encryption Helpers" checkbox

  3. Paste <SLACK_CHANNEL> into the slackChannel environment variable

  Note: The Slack channel does not contain private info, so do NOT click encrypt

  4. Paste <SLACK_HOOK_URL> into the kmsEncryptedHookUrl environment variable and click encrypt

  Note: You must exclude the protocol from the URL (e.g. "hooks.slack.com/services/abc123").

  5. Give your function's role permission for the kms:Decrypt action.

     Example:

    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1443036478000",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "<your KMS key ARN>"
            ]
        }
    ]
}
"""

ENCRYPTED_HOOK_URL = os.getenv("ENCRYPTED_HOOK_URL")
CHANNEL = os.getenv("CHANNEL")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Map the account number to name
ACCOUNT_MAP = {
    "671111111111": "Production",
    "672222222222": "Staging",
    "673333333333": "Development",
}


def lambda_handler(event, context):
    logger.info("Event: {}".format(event))
    contents = json.loads(event["Records"][0]["Sns"]["Message"])

    # Identify the type of the message by checking the following
    # Cloudwatch Alarm if contents['AlarmName'] exists
    # Trusted Advisor if contents['source'] = aws.trustedadvisor

    if contents.get("AlarmName", None):
        message = cloudwatch_alarm(contents)
    elif contents.get("source", None) == "aws.trustedadvisor":
        message = trusted_advisor(contents)
    else:
        # log that we failed to identify the message type
        message = "Unknown message format, check lambda execution logs"
        logger.error("Message: {}".format(contents))

    send_chat_notification(message, CHANNEL, ENCRYPTED_HOOK_URL)


def cloudwatch_alarm(contents):
    states_dict = {
        "OK": ":thumbsup:",
        "INSUFFICIENT_DATA": ":thinking_face:",
        "ALARM": ":fire:",
    }
    contents["OldStateValueIcon"] = states_dict.get(
        contents["OldStateValue"], contents["OldStateValue"]
    )
    contents["NewStateValueIcon"] = states_dict.get(
        contents["NewStateValue"], contents["NewStateValue"]
    )
    try:
        message = "*{alarm_name} - {state}*: {old_state} ⟶  {new_state}\n{reason}".format(
            alarm_name=contents["AlarmName"],
            state=contents["NewStateValue"],
            old_state=contents["OldStateValueIcon"],
            new_state=contents["NewStateValueIcon"],
            reason=contents["NewStateReason"],
        )
    except KeyError as e:
        logger.error(e)
        logger.error("Message: {}".format(contents))
        message = "Unknown Cloudwatch alarm message format, check lambda execution logs"

    return message


def trusted_advisor(contents):
    try:
        message = "*{check_name} triggered in {account}*\n{details}".format(
            check_name=contents["detail"]["check-name"],
            account=ACCOUNT_MAP.get(contents["account"], contents["account"]),
            details=convert_dict_to_text_block(contents["detail"]["check-item-detail"]),
        )
    except KeyError as e:
        logger.error(e)
        logger.error("Message: {}".format(contents))
        message = "Unknown Trusted adviser message format, check lambda execution logs"

    return message


def convert_dict_to_text_block(content_dict):
    """
    Convert the given dictionary to multiline text block
    of the format
    key1: value1
    key2: value2
    """
    message = ""
    for k, v in content_dict.items():
        message += "{}: _{}_\n".format(k, v)

    return message
