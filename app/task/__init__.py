from flask import Blueprint
task_bp = Blueprint("task_bp",__name__)

# Importing routes to attach them
from app.task import routes  