
from __future__ import print_function
import os, boto3, json, base64
import urllib.request, urllib.parse
import requests
import logging
from http import HTTPStatus

# https://github.com/terraform-aws-modules/terraform-aws-notify-slack/blob/master/functions/notify_slack.py

def cloudwatch_notification(message, region):
    states = {'OK': 'good', 'INSUFFICIENT_DATA': 'warning', 'ALARM': 'danger'}

    return {
        "color": states[message['NewStateValue']],
        "fallback": "Alarm {} triggered".format(message['AlarmName']),
        "fields": [
            { "title": "Alarm Name", "value": message['AlarmName'], "short": True },
            { "title": "Alarm Description", "value": message['AlarmDescription'], "short": False},
            { "title": "Alarm reason", "value": message['NewStateReason'], "short": False},
            { "title": "Old State", "value": message['OldStateValue'], "short": True },
            { "title": "Current State", "value": message['NewStateValue'], "short": True },
            {
                "title": "Link to Alarm",
                "value": "https://console.aws.amazon.com/cloudwatch/home?region=" + region + "#alarm:alarmFilter=ANY;name=" + urllib.parse.quote_plus
                    (message['AlarmName']),
                "short": False
            }
        ]
    }


def default_notification(subject, message):
    return {
        "fallback": "A new message",
        "fields": [{"title": subject if subject else "Message", "value": json.dumps(message), "short": False}]
    }


# Send a message to a slack channel
def notify_slack(subject, message, region):
    slack_url = os.environ['SLACK_WEBHOOK_URL']

    payload = {
        "attachments": []
    }
    if type(message) is str:
        try:
            message = json.loads(message)
        except json.JSONDecodeError as err:
            logging.exception(f'JSON decode error: {err}')
    if "AlarmName" in message:
        notification = cloudwatch_notification(message, region)
        payload['text'] = "AWS CloudWatch notification - " + message["AlarmName"]
        payload['attachments'].append(notification)
    else:
        payload['text'] = "AWS notification"
        payload['attachments'].append(default_notification(subject, message))
    resp = requests.post(slack_url, data=json.dumps(payload))
    return resp

def lambda_handler(event, context):
    subject = event['Records'][0]['Sns']['Subject']
    message = event['Records'][0]['Sns']['Message']
    region = event['Records'][0]['Sns']['TopicArn'].split(":")[3]
    resp = notify_slack(subject, message, region)
    return resp.status_code == HTTPStatus.ACCEPTED

# notify_slack({"AlarmName":"Example","AlarmDescription":"Example alarm description.","AWSAccountId":"000000000000","NewStateValue":"ALARM","NewStateReason":"Threshold Crossed","StateChangeTime":"2017-01-12T16:30:42.236+0000","Region":"EU - Ireland","OldStateValue":"OK"}, "eu-west-1")
# print(lambda_handler())

# Environment Variables to be declared on Lambda AWS Console: SLACK_WEBHOOK_URL

# Refer to this URL for more insights: https://api.slack.com/messaging/webhooks
# Easiest and quick way to integrate CloudWatch Alarms to be notified on Slack
# Implemented and tested as AWS Serverless Lambda Function
# Sunil Kumar Madikanti