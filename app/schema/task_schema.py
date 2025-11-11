from pydantic import BaseModel, validator , Field
from typing import Optional
from datetime import date
from app.models.task import PriorityEnum, StatusEnum

class TaskCreateSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    # status: str = StatusEnum.PENDING.value
    # priority: str = PriorityEnum.LOW.value
    status: StatusEnum = StatusEnum.PENDING  # ✅ Use Enum directly, not .value
    priority: PriorityEnum = PriorityEnum.LOW  # ✅ Use Enum directly
    start_date: Optional[date] = None
    due_date: Optional[date] = None
# When you use .value, you are storing the enum as a plain string.
# That means Pydantic loses all awareness that this field is an enum — it treats it like "PENDING" instead of StatusEnum.PENDING.

    @validator('status')
    def validate_status(cls, value):
        """Prevent creating tasks that are already completed or cancelled"""
        if value in [StatusEnum.COMPLETED, StatusEnum.CANCELLED]:
            raise ValueError('Cannot create a task with COMPLETED or CANCELLED status. New tasks must be PENDING or IN_PROGRESS.')
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

    class Config:
        use_enum_values = True  # ✅ This converts Enums to values automatically
# This tells Pydantic:
# “When serializing the model to JSON or dict, use the enum’s .value instead of the enum object.”

# So instead of returning this:
# {
#   "status": "StatusEnum.PENDING",
#   "priority": "PriorityEnum.LOW"
# }
# you’ll get this:
# {
#   "status": "PENDING",
#   "priority": "LOW"
# }



# title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     start_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
#     due_date = db.Column(db.DateTime, nullable=True)
#     priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.LOW)
#         status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING)



class TaskUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    # status: Optional[str] = None
    # priority: Optional[str] = None
    status: Optional[StatusEnum] = None  # ✅ Use Enum type
    priority: Optional[PriorityEnum] = None  # ✅ Use Enum type
    due_date: Optional[date] = None
    
    # @validator('status')
    # def validate_status(cls, v):
    #     if v and v not in [s.value for s in StatusEnum]:
    #         raise ValueError(f'Status must be one of: {[s.value for s in StatusEnum]}')
    #     return v
    
    # @validator('priority')
    # def validate_priority(cls, v):
    #     if v and v not in [p.value for p in PriorityEnum]:
    #         raise ValueError(f'Priority must be one of: {[p.value for p in PriorityEnum]}')
    #     return v
    
    class Config:
        use_enum_values = True


# class TaskReadSchema(BaseModel):
#     title: str = Field(...,min_length=1,max_length = 200)
#     description: Optional[str] = None
#     status: str = StatusEnum.PENDING.value
#     priority: str = PriorityEnum.LOW.value
#     start_date: date
#     due_date: Optional[date] = None

class TaskReadSchema(BaseModel):
    task_id: int
    title: str
    description: Optional[str]
    start_date: Optional[date]
    due_date: Optional[date]
    priority: PriorityEnum
    status: StatusEnum
    user_id: int

    class Config:
        use_enum_values = True
        from_attributes = True


