from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

class TwoFactorEnableRequest(BaseModel):
    password: str

class TwoFactorVerifyRequest(BaseModel):
    code: str
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Код должен содержать 6 цифр')
        return v

class TwoFactorDisableRequest(BaseModel):
    password: str

class EmailVerificationRequest(BaseModel):
    token: str

class TwoFactorLoginRequest(BaseModel):
    code: str
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Код должен содержать 6 цифр')
        return v

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

class TwoFactorStatusResponse(BaseModel):
    enabled: bool
    email_verified: bool

class EmailVerificationResponse(BaseModel):
    message: str
    success: bool
