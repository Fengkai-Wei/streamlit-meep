
from pydantic import BaseModel
from typing import Dict, Any


class UserLogin(BaseModel):

    username: str 
    password: str 


class JobSubmit(BaseModel):
    user_id: str          
    project_name: str     
    
    config: Dict[str, Any]