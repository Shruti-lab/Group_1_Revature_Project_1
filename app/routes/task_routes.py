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

#**************************************************************************************************
# Get all tasks for the user
@task_bp.route('/',methods=['GET'])
@jwt_required()     #Protects the route — user must be authenticated.
def get_tasks():
    try:
        user_id = get_jwt_identity()

        # Get query parameters
        status = request.args.get('status', type=str)
        priority = request.args.get('priority', type=str)
        search = request.args.get('search', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 5, type=int), 100)

        tasks = Task.query.filter_by(user_id=user_id)

        # Applying the task status filter
        if status:
            status = status.upper()
            if status not in [s.value for s in StatusEnum]:
                return error_response(
                    f'Invalid status. Must be one of: {[s.value for s in StatusEnum]}', 
                    400
                )
            tasks = tasks.filter_by(status=status)

        # Applying priority filter
        if priority:
            priority = priority.upper()
            if priority not in [p.value for p in PriorityEnum]:
                return error_response(
                    f'Invalid priority. Must be one of: {[p.value for p in PriorityEnum]}', 
                    400
                )
            tasks = tasks.filter_by(priority=priority)

        # Apply search filter by title or description
        if search:
            tasks = tasks.filter(
                db.or_(
                    db.or_(
                    Task.title.ilike(f'%{search}%'),
                    Task.description.ilike(f'%{search}%')
                )
                )
            )

        # getting total tasks count
        total = tasks.count()

        # Get paginated results
        tasks = tasks.order_by(Task.start_date.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page
        # OR total_pages = Math.ceil(total//per_page)
        
        return success_response(
            data={
                'tasks': [task.to_dict() for task in tasks.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_items': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            },
            message='Tasks retrieved successfully'
        )

            
    except Exception as e:
        return error_response(f'Failed to retrieve tasks: {str(e)}', 500)


       

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

# GET /overdue - tasks that are overdue (and not completed/cancelled)
@task_bp.route('/overdue', methods=['GET'])
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
