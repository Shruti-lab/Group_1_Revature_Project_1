from flask import Blueprint,request, jsonify
from app.models import Task
from app import db
from app.schema.task_schema import TaskCreateSchema, TaskReadSchema, TaskUpdateSchema
from app.utils.response import success_response, error_response
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity, jwt_required
<<<<<<< Updated upstream
=======
from datetime import date, datetime, timezone
from sqlalchemy import func
import logging

>>>>>>> Stashed changes
task_bp = Blueprint("task_bp",__name__)


# Base URL:- user/<userid>/tasks
# Base url:- user/tasks


# Get all tasks for the user
@task_bp.route('/',methods=['GET'])
@jwt_required()
def get_tasks():
	pass


# Get one task of the user
@task_bp.route('/<int:task_id>',methods=['GET'])
@jwt_required()
def get_one_task(task_id):
    try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()

        if not task:
            return error_response('Task not found', 404)

        return success_response(
            data=task.to_dict(),
            message="Task fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch task: {str(e)}", 500)
<<<<<<< Updated upstream
    
# Get tasks by status for the user
@task_bp.route('/status/<string:status>', methods=['GET'])
=======


#**************************************************************************************************


# GET /overdue - tasks that are overdue (and not completed/cancelled)
@task_bp.route('/overdue', methods=['GET'])
@jwt_required()
def get_overdue_tasks():
    user_id = get_jwt_identity()
    logger.info(f"Fetching overdue tasks for user id: {user_id}")
        
    try:
        # Fetch tasks that belong to user, have a due_date before today,
        # and are not COMPLETED or CANCELLED
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        overdue_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,             #must have a due date set.
            Task.due_date < today_start,       #due date is in the past.
            Task.status.notin_([StatusEnum.COMPLETED, StatusEnum.CANCELLED])
        ).order_by(Task.due_date.asc()).all()

        data = [t.to_dict() for t in overdue_tasks]     #sort soonest-overdue first, fetch all results.
        logger.info(f"Overdue tasks fetched - count: {len(data)} for user {user_id}")
        return success_response(data=data, message="Overdue tasks fetched")
    except Exception as e:
        logger.error(f"Failed to fetch overdue tasks for user {user_id}.")
        return error_response(f"Failed to fetch overdue tasks: {str(e)}", 500)


#**************************************************************************************************

# GET /today - tasks due today
@task_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_tasks():
    user_id = get_jwt_identity()
    logger.info(f"Fetching today's tasks for user_id: {user_id}")
        
    try:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
        today_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date >= today_start,
            Task.due_date <= today_end
        ).order_by(Task.due_date.asc()).all()

        data = [t.to_dict() for t in today_tasks]
        logger.info(f"Today's tasks fetched - count: {len(data)} for user {user_id}")
        return success_response(data=data, message="Today's tasks fetched")
    except Exception as e:
        logger.error(f"Failed to fetch today's tasks for user {user_id}.")
        return error_response(f"Failed to fetch today's tasks: {str(e)}", 500)


#**************************************************************************************************

# GET /stats - simple stats (counts by status + overdue count)
@task_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_task_stats():
    user_id = get_jwt_identity()
    logger.info(f"Fetching task statistics for user_id: {user_id}")
    
    try:
        # Count tasks grouped by status
        status_counts = db.session.query(
            Task.status, func.count(Task.task_id)
        ).filter_by(user_id=user_id).group_by(Task.status).all()   

        # Build dict: { 'PENDING': 10, 'COMPLETED': 4, ... }
        status_summary = {status.value 
                            if hasattr(status, 'value') 
                            else str(status): 
                            count
                        for status, count in status_counts}

        # total overdue
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        overdue_count = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date < today_start,
            Task.status.notin_([StatusEnum.COMPLETED, StatusEnum.CANCELLED])
        ).count()

        logger.info(f"Task stats fetched for user {user_id} - overdue: {overdue_count}")
        return success_response(
            data={
                "status_counts": status_summary,
                "overdue_count": overdue_count
            },
            message="Task stats fetched"
        )
    except Exception as e:
        logger.error(f"Failed to fetch stats for user {user_id}.")
        return error_response(f"Failed to fetch stats: {str(e)}", 500)


#**************************************************************************************************

# GET /recent - recent tasks created (optionally limit via ?limit=5)
@task_bp.route('/recent', methods=['GET'])
>>>>>>> Stashed changes
@jwt_required()
def get_tasks_by_status(status):
    try:
        user_id = get_jwt_identity()

        # Normalize status (optional, depends on your data format)
        status = status.capitalize()

        # Fetch all tasks with this status for the logged-in user
        tasks = Task.query.filter_by(user_id=user_id, status=status).all()

<<<<<<< Updated upstream
        if not tasks:
            return success_response(
                data=[],
                message=f"No tasks found with status '{status}'"
=======
    except Exception as e:
        logger.error(f"Failed to fetch recent tasks for user {user_id}.")
        return error_response(f"Failed to fetch recent tasks: {str(e)}", 500)


#**************************************************************************************************

#UPCOMING TASK 
# The purpose isn’t sorting — it’s filtering.
# It deliberately excludes everything that’s already due or overdue.
@task_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_tasks():
    """
    Get all upcoming tasks (due after today) for the logged-in user.
    Example: GET /user/tasks/upcoming
    """
    user_id = get_jwt_identity()
    logger.info(f"Fetching upcoming tasks for user_id: {user_id}")
    
    try:
        # today's date
        today = date.today()
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

        # fetch tasks that are due after today
        upcoming_tasks = (
            Task.query
            .filter(
                Task.user_id == user_id,
                Task.due_date != None,  # only consider tasks with a due date
                Task.due_date > today_end   # due date is in the future
>>>>>>> Stashed changes
            )

        task_list = [task.to_dict() for task in tasks]

        return success_response(
            data=task_list,
            message=f"Tasks with status '{status}' fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch tasks by status: {str(e)}", 500)


# Get tasks by priority for the user
@task_bp.route('/priority/<string:priority>', methods=['GET'])
@jwt_required()
def get_tasks_by_priority(priority):
    try:
        user_id = get_jwt_identity()

        # Normalize priority (optional, depending on your model values)
        priority = priority.capitalize()

        # Fetch tasks matching the given priority for this user
        tasks = Task.query.filter_by(user_id=user_id, priority=priority).all()

        if not tasks:
            return success_response(
                data=[],
                message=f"No tasks found with priority '{priority}'"
            )

        task_list = [task.to_dict() for task in tasks]

        return success_response(
            data=task_list,
            message=f"Tasks with priority '{priority}' fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch tasks by priority: {str(e)}", 500)


# Create a new task
@task_bp.route('/',methods=['POST'])
@jwt_required()
def create_task():
   try:
        # Validate request data
        data = TaskCreateSchema(**request.get_json())
        
        # Create new task
        user_id = get_jwt_identity()
        new_task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            user_id=user_id
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        return success_response(
            data=new_task.to_dict(),
            message='Task created successfully',
            status_code=201
        )

   except ValidationError as e:
      return error_response(message=str(e), status_code=400)
      




# Update one task of the user
@task_bp.route('/<int:task_id>',methods=['PUT'])
@jwt_required()
def update_task(task_id):
   try:
        user_id = get_jwt_identity()
        # Find task
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
        
        if not task:
            return error_response('Task not found', 404)
        
        # Validate request data
        data = TaskUpdateSchema(**request.get_json())

        print(data)
        
        # Update task fields
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status
        if data.priority is not None:
            task.priority = data.priority
        if data.due_date is not None:
            task.due_date = data.due_date
        
        db.session.commit()
        
        return success_response(
            data=task.to_dict(),
            message='Task updated successfully'
        )
        
   except ValidationError as e:
        return error_response('Validation failed', 400, errors=e.errors())
    
   except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update task: {str(e)}', 500)

   


# Delete one task of the user
@task_bp.route('/<int:task_id>',methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
   try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        print(task)
        
        if not task:
            return error_response('Task not found', 404)
        
        db.session.delete(task)
        db.session.commit()
        
        return success_response(
            message='Task deleted successfully'
        )
        
   except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete task: {str(e)}', 500)

