from app import db 
import enum
from datetime import datetime, timezone

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
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.LOW)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING)

    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    def is_overdue(self):
        """Check if task is overdue (timezone-aware comparison, correct enum checks)"""
        # If there's no due date or task already finished/cancelled => not overdue
        if not self.due_date:
            return False

        # self.status is an enum member; compare to enum members (not .value)
        if self.status in (StatusEnum.COMPLETED, StatusEnum.CANCELLED):
            return False

        # Ensure both sides are timezone-aware datetimes in UTC
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            # if stored as naive, assume UTC — safer to normalize
            due = due.replace(tzinfo=timezone.utc)

        return now > due

    def to_dict(self):
        """Serialize task to dictionary"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority.value if self.priority else None,
            'status': self.status.value if self.status else None,
            'user_id': self.user_id,
            'is_overdue': self.is_overdue() if self.due_date else False
        }

    def __repr__(self):
        return f"<Task {self.task_id} - {self.title} - {self.status.value}>"
