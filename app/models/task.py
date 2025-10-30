from app import db 
import enum
from datetime import datetime
from datetime import timezone

class PriorityEnum(enum.Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class StatusEnum(enum.Enum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.LOW)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING)

    def __repr__(self):
        return f"<Task {self.task_id} - {self.title} - {self.status.value}>"