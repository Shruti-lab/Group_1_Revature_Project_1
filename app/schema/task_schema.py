from pydantic import BaseModel, validator , Field
from typing import Optional ,List
from datetime import date
from app.models.task import PriorityEnum, StatusEnum


class TaskCreateSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    status: StatusEnum = StatusEnum.PENDING  # ✅ Use Enum directly, not .value
    priority: PriorityEnum = PriorityEnum.LOW  # ✅ Use Enum directly
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    images: Optional[List[str]] = []   

    @validator('status', pre=True, always=True)
    def validate_status(cls, value):
        """Prevent creating tasks that are already completed or cancelled"""
        if isinstance(value, str):
            value = value.upper()
        try:
            enum_value = StatusEnum(value)
        except ValueError:
            raise ValueError(f"Invalid status '{value}'. Must be one of {[s.value for s in StatusEnum]}")
        if enum_value in [StatusEnum.COMPLETED, StatusEnum.CANCELLED]:
            raise ValueError('Cannot create a task with COMPLETED or CANCELLED status.')
        return enum_value
    
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



class TaskUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[StatusEnum] = None  # ✅ Use Enum type
    priority: Optional[PriorityEnum] = None  # ✅ Use Enum type
    due_date: Optional[date] = None
    images: Optional[List[str]] = [] 
    
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


class TaskReadSchema(BaseModel):
    title: str = Field(...,min_length=1,max_length = 200)
    description: Optional[str] = None
    status: str = StatusEnum.PENDING.value
    priority: str = PriorityEnum.LOW.value
    start_date: date
    due_date: Optional[date] = None
    images: List[str] = []  

    



