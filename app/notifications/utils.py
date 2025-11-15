import os
import boto3
from datetime import datetime, timedelta

# create boto3 client with region from env (boto3 auto-loads credentials)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

sns_client = boto3.client("sns", region_name=AWS_REGION)


def build_tasks_message(tasks):
    """
    tasks: list of dict-like items with 'id','title','due_date' fields
    """
    if not tasks:
        return None
    lines = ["Here are your upcoming / overdue tasks:"]
    for t in tasks:
        # ensure due_date is string
        lines.append(f"- {t.get('title')} (due: {t.get('due_date')})")
    return "\n".join(lines)


def publish_to_topic(subject, message):
    if not SNS_TOPIC_ARN:
        raise RuntimeError("SNS_TOPIC_ARN not configured")
    resp = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
    return resp
