from pydantic import BaseModel, validator , Field
from typing import Optional
from datetime import datetime
from app.models.task import PriorityEnum, StatusEnum

class TaskCreateSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    status: str = StatusEnum.PENDING.value
    priority: str = PriorityEnum.LOW.value
    start_date: datetime
    due_date: Optional[datetime] = None


    @validator('status')
    def validate_satus(cls, value):
        if value and value not in [status.value for status in StatusEnum]:
            raise ValueError(f'Status must be one of: {[s.value for s in StatusEnum]}')
        return value
    
    @validator('priority')
    def validate_priority(cls, value):
        if value and value not in [priority.value for priority in PriorityEnum]:
            raise ValueError(f'Priority must be one of: {[p.value for p in PriorityEnum]}')
        return value
    
    @validator('due_date')
    def validate_due_date(cls, value):
        if value and value < datetime.now():
            raise ValueError('Due date cannot be in the past.')
        return value




# title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     start_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
#     due_date = db.Column(db.DateTime, nullable=True)
#     priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.LOW)
#         status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING)



class TaskUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in [s.value for s in StatusEnum]:
            raise ValueError(f'Status must be one of: {[s.value for s in StatusEnum]}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v and v not in [p.value for p in PriorityEnum]:
            raise ValueError(f'Priority must be one of: {[p.value for p in PriorityEnum]}')
        return v
    


class TaskReadSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    status: str = StatusEnum.PENDING.value
    priority: str = PriorityEnum.LOW.value
    start_date: datetime
    due_date: Optional[datetime] = None

    



