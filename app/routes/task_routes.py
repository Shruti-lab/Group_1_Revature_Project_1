from flask import Blueprint,request, jsonify
from app.models import Task
from app import db
from app.schema.task_schema import TaskCreateSchema, TaskReadSchema, TaskUpdateSchema
from app.utils.response import success_response, error_response
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity, jwt_required
task_bp = Blueprint("task_bp",__name__)


# Base URL:- user/<userid>/tasks
# Base url:- user/tasks


# Get all tasks for the user
@task_bp.route('/',methods=['GET'])
@jwt_required()
def get_tasks():
   return "Got all task!"


# Get one task of the user
@task_bp.route('/<int:task_id>',methods=['GET'])
@jwt_required()
def get_one_task(task_id):
   pass


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

