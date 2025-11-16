from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
from app.models.task import Task, StatusEnum
from app.models.user import User
from app import db
import boto3
import os
logger = logging.getLogger(__name__)

def start_scheduler(flask_app):
    """
    Start a background scheduler for sending notifications.
    The scheduler runs jobs defined here.
    """
    scheduler = BackgroundScheduler()

    def job_wrapper():
        """Wrapper to execute notification job within Flask app context"""
        with flask_app.app_context():
            try:


                now = datetime.utcnow()
                upcoming_boundary = now + timedelta(days=1)

                users = User.query.all()

                for user in users:
                    if not user.sns_topic_arn:
                        continue

                    tasks = Task.query.filter(
                    Task.user_id == user.user_id,
                    Task.status.in_([StatusEnum.PENDING]),
                    Task.due_date != None,
                    Task.due_date <= upcoming_boundary,
                    Task.due_date >= now  
                    ).all()

                    message_lines = [f"[REMINDER] You have {len(tasks)} task(s) due soon!\n"]
                    for t in tasks:
                        message_lines.append(
                            f"- {t.title} (Due: {t.due_date.strftime('%Y-%m-%d')})"
                        )

                    message = "\n".join(message_lines)

                    try:
                        sns = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))
                        sns.publish(
                            TopicArn=user.sns_topic_arn,
                            Subject="[TaskFlow] Task Reminder: Upcoming Due Tasks",
                            Message=message
                        )
                        logger.info(f"Notification sent to user {user.user_id} ({user.email})")
                    except Exception as e:
                        logger.error(f"Failed to send SNS notification to user {user.user_id}: {str(e)}")

                logger.info(f"[{datetime.utcnow().isoformat()}] SNS notification job executed successfully")

            except Exception as e:
                logger.error(f"Error in scheduler job: {str(e)}", exc_info=True)

    scheduler.add_job(job_wrapper, 'cron', hour=7, minute=0)

    # Uncomment for testing: run every minute
    # scheduler.add_job(job_wrapper, 'interval', minutes=2)

    try:
        scheduler.start()
        logger.info("[OK] Background scheduler started successfully")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start scheduler: {str(e)}", exc_info=True)

    return scheduler

