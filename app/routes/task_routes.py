from app.models.task import StatusEnum, PriorityEnum
from flask import Blueprint,request
from app.models import Task
from app import db
from app.schema.task_schema import TaskCreateSchema, TaskReadSchema, TaskUpdateSchema
from app.utils.response import success_response, error_response
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import date, datetime
from sqlalchemy import func

task_bp = Blueprint("task_bp",__name__)


# Base url:- user/tasks
# Base url:- user/tasks

#**************************************************************************************************
# Get all tasks for the user
@task_bp.route('/',methods=['GET'])
@jwt_required()     #Protects the route — user must be authenticated.
def get_tasks():
    try:
        user_id = get_jwt_identity()  #Retrieves the identity stored inside the JWT,get users task

        # --- Filtering parameters ---
        status = request.args.get('status', type=str)
        priority = request.args.get('priority', type=str)
        search = request.args.get('search', type=str)  # optional title search ,(used to search the title)
        page = request.args.get('page', default=1, type=int)          #Reads page query param for pagination.
        per_page = request.args.get('per_page', default=10, type=int)   #(items per page). Defaults to 10

        # --- Base query ---
        query = Task.query.filter_by(user_id=user_id)   #selecting tasks that belong to this user_id.

        # --- Apply filters ---
        if status:
            try:
                query = query.filter(Task.status == StatusEnum(status.upper())) #filter tasks whose status equals that enum value, StatusEnum(status.upper()) — converts text like "completed" -> "COMPLETED" and into the Enum member.
            except ValueError:
                return error_response(f"Invalid status '{status}'.", 400)

        if priority:
            try:
                query = query.filter(Task.priority == PriorityEnum(priority.upper())) #same as above 
            except ValueError:
                return error_response(f"Invalid priority '{priority}'.", 400)

        if search:
            query = query.filter(Task.title.ilike(f"%{search}%")) #Adds a case-insensitive LIKE filter on title. This will return tasks whose title contains the search substring.

        # --- Pagination ---
        paginated = query.order_by(Task.due_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
        # Orders query results by due_date ascending (soonest due first)
        # then uses SQLAlchemy/Flask-SQLAlchemy paginate to get a page object containing only the requested slice of results.
        # error_out=False prevents 404 on out-of-range pages — it returns an empty list instead.
        tasks = [task.to_dict() for task in paginated.items]
        # Serializes each Task model instance into a dictionary using your model's to_dict() method (so JSON is safe to return).

        return success_response(
            data={
                "tasks": tasks,
                "page": page,
                "total_pages": paginated.pages,
                "total_tasks": paginated.total
            },
            message="Tasks fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch tasks: {str(e)}", 500)



#**************************************************************************************************


# Get one task of the user
@task_bp.route('/<int:task_id>',methods=['GET'])
@jwt_required()
def get_one_task(task_id):
    try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()

        if not task:
            return error_response('Task not found', 404)

        return success_response(
            data=task.to_dict(),
            message="Task fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch task: {str(e)}", 500)


#**************************************************************************************************


# GET /overdue - tasks that are overdue (and not completed/cancelled)
@task_bp.route('/overdue', methods=['GET'])
@jwt_required()
def get_overdue_tasks():
    try:
        user_id = get_jwt_identity()
        # Fetch tasks that belong to user, have a due_date before today,
        # and are not COMPLETED or CANCELLED
        overdue_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,             #must have a due date set.
            Task.due_date < date.today(),      #due date is in the past.
            Task.status.notin_([StatusEnum.COMPLETED, StatusEnum.CANCELLED])
        ).order_by(Task.due_date.asc()).all()

        data = [t.to_dict() for t in overdue_tasks]     #sort soonest-overdue first, fetch all results.
        return success_response(data=data, message="Overdue tasks fetched")
    except Exception as e:
        return error_response(f"Failed to fetch overdue tasks: {str(e)}", 500)


#**************************************************************************************************

# GET /today - tasks due today
@task_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_tasks():
    try:
        user_id = get_jwt_identity()
        today = date.today()
        today_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date == date.today()
        ).order_by(Task.due_date.asc()).all()

        return success_response(data=[t.to_dict() for t in today_tasks], message="Today's tasks fetched")
    except Exception as e:
        return error_response(f"Failed to fetch today's tasks: {str(e)}", 500)


#**************************************************************************************************

# GET /stats - simple stats (counts by status + overdue count)
@task_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_task_stats():
    try:
        user_id = get_jwt_identity()
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
        overdue_count = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date < date.today(),
            Task.status.notin_([StatusEnum.COMPLETED, StatusEnum.CANCELLED])
        ).count()

        return success_response(
            data={
                "status_counts": status_summary,
                "overdue_count": overdue_count
            },
            message="Task stats fetched"
        )
    except Exception as e:
        return error_response(f"Failed to fetch stats: {str(e)}", 500)


#**************************************************************************************************

# GET /recent - recent tasks created (optionally limit via ?limit=5)
@task_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_tasks():
    """
    Get the most recent tasks for the logged-in user.
    Ordered by task_id DESC (newest first) and limited by ?limit=.
    Example: /recent?limit=5
    """
    try:
        user_id = get_jwt_identity()
        
        # Read 'limit' from query string, default to 5
        limit = request.args.get('limit', default=5, type=int)

        # Query user's tasks, order by descending task_id, and limit results
        recent_tasks = (
            Task.query
            .filter_by(user_id=user_id)
            .order_by(Task.task_id.desc())
            .limit(limit)
            .all()
        )

        # Convert to dictionaries for JSON response
        data = [task.to_dict() for task in recent_tasks]

        return success_response(data=data, message="Recent tasks fetched successfully")

    except Exception as e:
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
    try:
        user_id = get_jwt_identity()

        # today's date
        today = date.today()

        # fetch tasks that are due after today
        upcoming_tasks = (
            Task.query
            .filter(
                Task.user_id == user_id,
                Task.due_date != None,  # only consider tasks with a due date
                Task.due_date > today   # due date is in the future
            )
            .order_by(Task.due_date.asc())  # sort earliest upcoming first
            .all()
        )

        data = [task.to_dict() for task in upcoming_tasks]

        return success_response(
            data=data,
            message="Upcoming tasks fetched successfully"
        )

    except Exception as e:
        return error_response(f"Failed to fetch upcoming tasks: {str(e)}", 500)


#**************************************************************************************************


# Create a new task
@task_bp.route('/',methods=['POST'])
@jwt_required()
def create_task():
    try:
        # Validate request data
        payload = request.get_json()
        data = TaskCreateSchema(**payload)
        
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
        first_error = e.errors()[0]
        message = first_error.get('msg', 'Invalid input')
        return error_response(message, 400)
    
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create task: {str(e)}', 500)





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
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
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


# Delete multiple tasks of the user
@task_bp.route('/bulk_delete', methods=['DELETE'])
@jwt_required()
def bulk_delete():
    try:
        user_id = get_jwt_identity()
        ids_str = request.args.get('task_ids')

        if not ids_str:
            return error_response("task_ids query parameter required", 400)

        task_ids = [int(i) for i in ids_str.split(',')]
        tasks = Task.query.filter(Task.task_id.in_(task_ids), Task.user_id == user_id).all()

        if not tasks:
            return error_response("No valid tasks found to delete", 404)

        for task in tasks:
            db.session.delete(task)
        db.session.commit()

        return success_response(message=f"Deleted {len(tasks)} tasks")

    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to delete tasks: {str(e)}", 500)
