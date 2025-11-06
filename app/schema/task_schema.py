from pydantic import BaseModel, validator , Field
from typing import Optional
from datetime import date
from app.models.task import PriorityEnum, StatusEnum

class TaskCreateSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    status: str = StatusEnum.PENDING.value
    priority: str = PriorityEnum.LOW.value
    start_date: Optional[date] = None
    due_date: Optional[date] = None


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
        if value and value < date.today():
            raise ValueError('Due date cannot be in the past.')
        return value




class TaskUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    
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
    start_date: date
    due_date: Optional[date] = None

    



