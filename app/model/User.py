from pydantic import BaseModel, Field, field_validator


class UserRole(str):
    """Роль пользователя в системе. Может быть 'admin' или 'user'.

    Args:
        str (str): Передаваемое значение
    """

    ADMIN = "admin"
    USER = "user"


class Users(BaseModel):
    username: str = Field(min_length=4, max_length=100, example="john_doe")
    email: str = Field(min_length=4, max_length=20, example="john.doe@example.com")
    role: UserRole = Field(
        default=UserRole.USER,
        example=UserRole.USER,
        description="Role of the user, either 'admin' or 'user'",
    )

    @classmethod
    @field_validator("role", mode="before")
    def validate_role(cls, v):
        pass
