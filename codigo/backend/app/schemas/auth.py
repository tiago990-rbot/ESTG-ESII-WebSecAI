from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=16, max_length=128)
    confirmation: str = Field(min_length=16, max_length=128)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]{43}$")
    new_password: str = Field(min_length=16, max_length=128)
    confirmation: str = Field(min_length=16, max_length=128)
