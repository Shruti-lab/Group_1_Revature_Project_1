from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta ,timezone
from app.models.task import Task, StatusEnum
from app.models.user import User
from app import db
from flask_jwt_extended import get_jwt_identity, jwt_required
import boto3
import os
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint("notifications", __name__)

def topic_exists(sns, topic_arn):
    try:
        sns.get_topic_attributes(TopicArn=topic_arn)
        return True
    except Exception:
        return False


def check_subscription_status(sns, topic_arn, email):
    """Return: confirmed | pending | none"""

    try:
        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
    except Exception:
        return "none"  

    for sub in subs.get("Subscriptions", []):
        if sub["Endpoint"].lower() == email.lower():
            arn = sub["SubscriptionArn"]

            if arn == "PendingConfirmation":
                return "pending"
            if arn.startswith("arn:aws:sns"):
                return "confirmed"

    return "none"



# ------------------------------------------------------
# Main subscribe endpoint
# ------------------------------------------------------
@notifications_bp.route("/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if not user.email:
            return jsonify({"success": False, "error": "User has no email"}), 400

        sns = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))

        topic_arn = user.sns_topic_arn

        if (
            not topic_arn
            or not isinstance(topic_arn, str)
            or not topic_arn.startswith("arn:aws:sns")
            or not topic_exists(sns, topic_arn)
        ):
            topic = sns.create_topic(Name=f"user_{user.user_id}_notifications")
            topic_arn = topic.get("TopicArn")

            if not topic_arn or not topic_arn.startswith("arn:aws:sns"):
                raise Exception("SNS returned an invalid TopicArn")

            user.sns_topic_arn = topic_arn
            db.session.commit()

        status = check_subscription_status(sns, topic_arn, user.email)

        if status == "confirmed":
            return jsonify({
                "success": True,
                "topic_arn": topic_arn,
                "subscription": "Email already subscribed"
            }), 200

        if status == "pending":
            return jsonify({
                "success": True,
                "topic_arn": topic_arn,
                "subscription": "Email pending confirmation"
            }), 200

        sub = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=user.email
        )

        return jsonify({
            "success": True,
            "topic_arn": topic_arn,
            "subscription": "Confirmation email sent",
            "subscription_arn": sub.get("SubscriptionArn")
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notifications_bp.route("/subscription/status", methods=["GET"])
@jwt_required()
def subscription_status():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"success": False, "status": "none", "error": "User not found"}), 404

        if not user.sns_topic_arn:
            return jsonify({"success": True, "status": "none"}), 200

        sns = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))

        status = check_subscription_status(sns, user.sns_topic_arn, user.email)

        return jsonify({
            "success": True,
            "status": status
        }), 200

    except Exception as e:
        return jsonify({"success": False, "status": "none", "error": str(e)}), 500

@notifications_bp.route("/unsubscribe", methods=["POST"])
@jwt_required()
def unsubscribe():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if not user.email:
            return jsonify({"success": False, "error": "User has no email"}), 400

        topic_arn = user.sns_topic_arn

        if not topic_arn:
            return jsonify({
                "success": False,
                "error": "You are not subscribed to any notifications.",
            }), 400

        if not topic_arn.startswith("arn:aws:sns"):
            return jsonify({
                "success": False,
                "error": "Invalid SNS TopicArn found in database."
            }), 400

        sns = boto3.client("sns", region_name="us-east-1")

        if not topic_exists(sns, topic_arn):
            user.sns_topic_arn = None
            db.session.commit()

            return jsonify({
                "success": False,
                "error": "SNS topic does not exist anymore.",
                "action_required": "Please subscribe again."
            }), 400

        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)

        subscription_arn = None
        for sub in subs.get("Subscriptions", []):
            if sub["Endpoint"].lower() == user.email.lower():
                subscription_arn = sub["SubscriptionArn"]
                break

        if not subscription_arn:
            return jsonify({
                "success": False,
                "error": "Your email is not subscribed to this topic."
            }), 400

        if subscription_arn == "PendingConfirmation":
            return jsonify({
                "success": False,
                "error": "Subscription not confirmed.",
                "info": "You cannot unsubscribe until the email subscription is confirmed."
            }), 400

        sns.unsubscribe(SubscriptionArn=subscription_arn)

        user.sns_topic_arn = None
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Successfully unsubscribed from notifications.",
            "unsubscribed_email": user.email
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@notifications_bp.route("/pending", methods=["GET"])
@jwt_required()
def get_pending_notifications():
    
    import traceback

    try:
        current_user_id = get_jwt_identity()
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).date()

        start_of_tomorrow = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
        end_of_tomorrow = datetime.combine(tomorrow, datetime.max.time(), tzinfo=timezone.utc)

        tasks = Task.query.filter(
            Task.user_id == current_user_id,
            Task.status == StatusEnum.PENDING,
            Task.due_date >= start_of_tomorrow,
            Task.due_date <= end_of_tomorrow
        ).order_by(Task.due_date).all()

        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if not user.sns_topic_arn:
            return jsonify({
                "success": False,
                "error": "You are not subscribed to our notification services.",
                "action_required": "Go to /subscribe and confirm your email subscription."
            }), 400

        sns = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))

        try:
            subs = sns.list_subscriptions_by_topic(TopicArn=user.sns_topic_arn)
        except Exception:
            return jsonify({
                "success": False,
                "error": "SNS topic invalid or deleted.",
                "action_required": "Please resubscribe."
            }), 400

        subscription_status = "none"

        for sub in subs.get("Subscriptions", []):
            if sub["Endpoint"].lower() == user.email.lower():
                arn = sub["SubscriptionArn"]
                if arn == "PendingConfirmation":
                    subscription_status = "pending"
                elif arn.startswith("arn:aws:sns"):
                    subscription_status = "confirmed"
                break

        if subscription_status == "none":
            return jsonify({
                "success": False,
                "error": "You are not subscribed to our notification services.",
                "action_required": "Go to /subscribe and confirm your email subscription."
            }), 400

        if subscription_status == "pending":
            return jsonify({
                "success": False,
                "error": "You have not confirmed your notification subscription.",
                "action_required": "Please check your email and confirm the SNS subscription.",
                "info": "Only after confirming your subscription will you see pending tasks."
            }), 400


        if not tasks:
            return jsonify({
                "success": True,
                "user_id": current_user_id,
                "message": "No upcoming or due tasks within 24 hours.",
                "pending_tasks": []
            }), 200

        message_lines = [
            f"You have {len(tasks)} task(s) due within 24 hours:\n"
        ]
        task_list = []

        for t in tasks:
            task_list.append({
                "task_id": t.task_id,
                "title": t.title,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "priority": t.priority.value,
                "status": t.status.value
            })

            message_lines.append(
                f"- {t.title} (Due: {t.due_date.strftime('%Y-%m-%d')})"
            )

        message_text = "\n".join(message_lines)

        sns.publish(
            TopicArn=user.sns_topic_arn,
            Subject="⏰ Task Reminder: Upcoming Due Tasks",
            Message=message_text
        )

        return jsonify({
            "success": True,
            "user_email": user.email,
            "tasks_count": len(tasks),
            "pending_tasks": task_list,
            "message_sent": message_text
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
 
@notifications_bp.route("/send", methods=["POST"])
@jwt_required()
def send_notification():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
 
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
 
        topic_arn = user.sns_topic_arn
        print("User TopicArn:", topic_arn)
 
        if not topic_arn:
            return jsonify({
                    "success": False,
                    "error": "You are not subscribed to our notification services.",
                    "action_required": "Go to /subscribe and confirm your email subscription."
            }), 400
 
        sns = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))
 
        try:
            subs = sns.list_subscriptions_by_topic(TopicArn=user.sns_topic_arn)
        except Exception:
            return jsonify({
                "success": False,
                "error": "SNS topic invalid or deleted.",
                "action_required": "Please resubscribe."
            }), 400
 
        subscription_status = "none"
 
        for sub in subs.get("Subscriptions", []):
            if sub["Endpoint"].lower() == user.email.lower():
                arn = sub["SubscriptionArn"]
                if arn == "PendingConfirmation":
                    subscription_status = "pending"
                elif arn.startswith("arn:aws:sns"):
                    subscription_status = "confirmed"
                break
 
        if subscription_status == "none":
            return jsonify({
                "success": False,
                "error": "You are not subscribed to task notifications.",
                "action_required": "Go to /subscribe to subscribe and confirm your email."
            }), 400
 
        if subscription_status == "pending":
            return jsonify({
                "success": False,
                "error": "Your subscription is pending confirmation.",
                "action_required": "Check your email and click 'Confirm subscription'.",
                "info": "You must confirm before receiving notifications."
            }), 400

 
        data = request.get_json(silent=True) or {}
        message = (
            data.get("message") or
            request.headers.get("message") or
            "No message provided"
        )
 
        sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject="TaskFlow Notification"
        )
 
        return jsonify({
            "success": True,
            "message": "Notification sent successfully",
            "topic_arn": topic_arn
        }), 200
 
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
 