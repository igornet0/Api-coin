from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, model_validator
from datetime import datetime

class UserLoginResponse(BaseModel):
    name: str
    login: str
    email: str
    password: str

class LoginRequest(BaseModel):
    login: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    password: str
    
    @model_validator(mode='after')
    def validate_at_least_one_identifier(self):
        if not self.login and not self.email and not self.username:
            raise ValueError('Either login, email, or username must be provided')
        return self

class UserResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    name: str
    login: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created: datetime
    
class TokenData(BaseModel):
    email: Optional[str] = None
    login: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

    message: str = "User logged in successfully"


class KucoinApiKeyCreate(BaseModel):
    name: str
    api_key: str
    api_secret: str
    api_passphrase: str
    limit_requests: int = 1000
    timedelta_refresh: int = 60  # в минутах


class KucoinApiKeyResponse(BaseModel):
    id: int
    name: str
    api_key: str
    is_active: bool
    limit_requests: int
    requests_count: int
    timedelta_refresh: int
    next_refresh: datetime
