from app.models.task import StatusEnum, PriorityEnum
from flask import Blueprint,request
from app.models import Task
from app import db
from app.schema.task_schema import TaskCreateSchema, TaskReadSchema, TaskUpdateSchema
from app.utils.response import success_response, error_response
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import date, datetime,timezone
from sqlalchemy import func
from app.utils.s3_helper import upload_to_s3,delete_from_s3
import logging

task_bp = Blueprint("task_bp",__name__)
logger = logging.getLogger(__name__)



# Base url:- user/tasks
# Base url:- user/tasks

#**************************************************************************************************
# Get all tasks for the user
@task_bp.route('/',methods=['GET'])
@jwt_required()     #Protects the route — user must be authenticated.
def get_tasks():
    user_id = get_jwt_identity()  #Retrieves the identity stored inside the JWT,get users task
    logger.info(f"Fetching tasks for user id: {user_id}")

    try:
        # --- Filtering parameters ---
        status = request.args.get('status', type=str)
        priority = request.args.get('priority', type=str)
        search = request.args.get('search', type=str)  # optional title search ,(used to search the title)
        page = request.args.get('page', default=1, type=int)          #Reads page query param for pagination.
        per_page = request.args.get('per_page', default=10, type=int)   #(items per page). Defaults to 10

        logger.info(f"Filter params - status: {status}, priority: {priority}, search: {search}, page: {page}")

        # --- Base query ---
        query = Task.query.filter_by(user_id=user_id)   #selecting tasks that belong to this user_id.

        # --- Apply filters ---
        if status:
            try:
                #filter tasks whose status equals that enum value, StatusEnum(status.upper()) — converts text like "completed" -> "COMPLETED" and into the Enum member.
                query = query.filter(Task.status == StatusEnum(status.upper())) 
                logger.info(f"Applied status filter: {status}")
            except ValueError:
                logger.warning(f"Invalid status filter attempted: {status}")
                return error_response(f"Invalid status '{status}'.", 400)

        if priority:
            try:
                #same as above
                query = query.filter(Task.priority == PriorityEnum(priority.upper()))  
                logger.info(f"Applied priority filter: {priority}")
            except ValueError:
                logger.warning(f"Invalid priority filter attempted: {priority}")
                return error_response(f"Invalid priority '{priority}'.", 400)

        if search:
            #Adds a case-insensitive LIKE filter on title. This will return tasks whose title contains the search substring.
            query = query.filter(Task.title.ilike(f"%{search}%")) 
            logger.info(f"Applied search filter: {search}")

        # --- Pagination ---
        paginated = query.order_by(Task.due_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
        # Orders query results by due_date ascending (soonest due first)
        # then uses SQLAlchemy/Flask-SQLAlchemy paginate to get a page object containing only the requested slice of results.
        # error_out=False prevents 404 on out-of-range pages — it returns an empty list instead.
        tasks = [task.to_dict() for task in paginated.items]
        # Serializes each Task model instance into a dictionary using your model's to_dict() method (so JSON is safe to return).

        logger.info(f"Tasks fetched successfully - count: {len(tasks)}, total: {paginated.total}")
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
        logger.error(f"Failed to fetch tasks for user {user_id}: {str(e)}")
        return error_response(f"Failed to fetch tasks: {str(e)}", 500)



#**************************************************************************************************


# Get one task of the user
@task_bp.route('/<int:task_id>',methods=['GET'])
@jwt_required()
def get_one_task(task_id):
    user_id = get_jwt_identity()
    logger.info(f"Fetching task {task_id} for user id: {user_id}")
    
    try:
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()

        if not task:
            logger.warning(f"Task not found - task_id: {task_id}, user id: {user_id}")
            return error_response('Task not found', 404)

        logger.info(f"Task {task_id} fetched successfully for user id {user_id}")
        return success_response(
            data=task.to_dict(),
            message="Task fetched successfully"
        )

    except Exception as e:
        logger.error(f"Failed to fetch task {task_id} for user {user_id}.")
        return error_response(f"Failed to fetch task: {str(e)}", 500)


#**************************************************************************************************


# GET /overdue - tasks that are overdue (and not completed/cancelled)
@task_bp.route('/overdue', methods=['GET'])
@jwt_required()
def get_overdue_tasks():
    user_id = get_jwt_identity()
    logger.info(f"Fetching overdue tasks for user id: {user_id}")

    try:
        # Fetch all tasks for the user
        tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status.notin_([StatusEnum.COMPLETED, StatusEnum.CANCELLED]),
            Task.due_date != None
        ).all()

        # Filter overdue using your model’s timezone-safe logic
        overdue_tasks = [t for t in tasks if t.is_overdue()]

        data = [t.to_dict() for t in overdue_tasks]

        logger.info(f"Overdue tasks fetched - count: {len(data)} for user {user_id}")
        return success_response(data=data, message="Overdue tasks fetched")

    except Exception as e:
        logger.error(f"Failed to fetch overdue tasks for user {user_id}: {str(e)}")
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
        today_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date == date.today()
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
        overdue_count = Task.query.filter(
            Task.user_id == user_id,
            Task.due_date != None,
            Task.due_date < date.today(),
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
@jwt_required()
def get_recent_tasks():
    """
    Get the most recent tasks for the logged-in user.
    Ordered by task_id DESC (newest first) and limited by ?limit=.
    Example: /recent?limit=5
    """
    user_id = get_jwt_identity()
        
    # Read 'limit' from query string, default to 5
    limit = request.args.get('limit', default=5, type=int)
    logger.info(f"Fetching recent tasks for user_id: {user_id}, limit: {limit}.")
    
    try:
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

        logger.info(f"Recent tasks fetched - count: {len(data)} for user {user_id}")
        return success_response(data=data, message="Recent tasks fetched successfully")

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

        logger.info(f"Upcoming tasks fetched - count: {len(data)} for user {user_id}")

        return success_response(
            data=data,
            message="Upcoming tasks fetched successfully"
        )

    except Exception as e:
        logger.error(f"Failed to fetch upcoming tasks for user {user_id}.")
        return error_response(f"Failed to fetch upcoming tasks: {str(e)}", 500)


#**************************************************************************************************


# Create a new task
@task_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    logger.info(f"Creating new task for user_id: {user_id}")

    try:
        # Validate request data
        data = TaskCreateSchema(**request.form.to_dict())  

        # Handle multiple files
        files = request.files.getlist("images")  
        image_urls = []

        for file in files:
            url = upload_to_s3(file) 
            image_urls.append(url)

        # Create new task
        user_id = get_jwt_identity()
        new_task = Task(
            title=data.title,
            description=data.description,
            status=StatusEnum.PENDING,
            priority=data.priority,
            due_date=data.due_date,
            user_id=user_id,
            images=image_urls  
        )
        db.session.add(new_task)
        db.session.commit()

        logger.info(f"Task created successfully - task_id: {new_task.task_id} for user {user_id}")
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




from sqlalchemy.orm.attributes import flag_modified

@task_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    logger.info(f"Updating task {task_id} for user_id: {user_id}")
        
    try:
        # Find task
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()

        if not task:
            logger.warning(f"Task not found for update - task_id: {task_id}, user_id: {user_id}")
            return error_response('Task not found', 404)

        data = TaskUpdateSchema(**request.form.to_dict())

        files = request.files.getlist("images")
        image_urls = []
        for file in files:
            if file and file.filename:
                url = upload_to_s3(file)
                if url:
                    image_urls.append(url)

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status
            task.status = StatusEnum(data.status.upper())
        if data.priority is not None:
            task.priority = data.priority
            task.priority = PriorityEnum(data.priority.upper())
        if data.due_date is not None:
            task.due_date = data.due_date

 
        if image_urls:
            if not task.images:
                task.images = []
            task.images.extend(image_urls)
            flag_modified(task, "images")
        db.session.commit()

        logger.info(f"Task {task_id} updated successfully for user id {user_id}, fields: {task}")
        return success_response(
            data=task.to_dict(),
            message='Task updated successfully'
        )
        
    except ValidationError as e:
        # Formatng validation errors properly
        logger.warning(f"Task update validation failed for task {task_id}.")
        errors = []
        print(e.errors())
        for error in e.errors():
            errors.append({
                'field': error['loc'][0] if error['loc'] else 'unknown',
                'message': error['msg'],
                'type': error['type']
            })
        return error_response('Validation failed', 400, errors=errors)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update task {task_id} for user {user_id}.")
        return error_response(f'Failed to update task: {str(e)}', 500)

    


# Delete one task of the user
@task_bp.route('/<int:task_id>',methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    logger.info(f"Deleting task {task_id} for user id: {user_id}")
    
    try:
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
        print(task)
        
        if not task:
            logger.warning(f"Task not found for deletion - task_id: {task_id}, user_id: {user_id}")
            return error_response('Task not found', 404)
        
        if task.images:
            delete_from_s3(task.images)

        db.session.delete(task)
        db.session.commit()

        logger.info(f"Task {task_id} deleted successfully for user {user_id}")
        return success_response(
            message='Task deleted successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete task {task_id} for user {user_id}.")
        return error_response(f'Failed to delete task: {str(e)}', 500)


# Delete multiple tasks of the user
@task_bp.route('/bulk_delete', methods=['DELETE'])
@jwt_required()
def bulk_delete():
    user_id = get_jwt_identity()
    ids_str = request.args.get('task_ids')
    logger.info(f"Bulk deleting tasks for user_id: {user_id}, task_ids: {ids_str}")

    try:
        if not ids_str:
            logger.warning(f"Bulk delete attempted without task_ids for user {user_id}")
            return error_response("task_ids query parameter required", 400)

        task_ids = [int(i) for i in ids_str.split(',')]
        tasks = Task.query.filter(Task.task_id.in_(task_ids), Task.user_id == user_id).all()

        if not tasks:
            logger.warning(f"No valid tasks found for bulk delete - user {user_id}, ids: {task_ids}")
            return error_response("No valid tasks found to delete", 404)

        for task in tasks:
            if task.images:
                 delete_from_s3(task.images)
            db.session.delete(task)
        db.session.commit()

        logger.info(f"Bulk deleted {len(tasks)} tasks for user {user_id}")
        return success_response(message=f"Deleted {len(tasks)} tasks")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed bulk delete for user {user_id}.")
        return error_response(f"Failed to delete tasks: {str(e)}", 500)
