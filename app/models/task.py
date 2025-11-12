from app import db 
import enum
from datetime import datetime, date, timezone

class PriorityEnum(enum.Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class StatusEnum(enum.Enum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, default=datetime.now(timezone.utc))
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.LOW)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING)

    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    # New field: images (store array of S3 URLs)
    images = db.Column(db.JSON, default=[]) 

    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in [StatusEnum.COMPLETED, StatusEnum.CANCELLED]:
            return date.today() > self.due_date
        return False
    

    def to_dict(self):
        """Serialize task to dictionary"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority.value,
            'status': self.status.value,
            'user_id': self.user_id,
            'images': self.images, 
            'is_overdue': self.is_overdue()
        }

    def __repr__(self):
        return f"<Task {self.task_id} - {self.title} - {self.status.value}>"