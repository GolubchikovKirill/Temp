import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class KanbanProjectBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class KanbanProjectCreate(KanbanProjectBase):
    pass


class KanbanProjectUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]
    description: str | None = Field(default=None, max_length=1000)


class KanbanProject(KanbanProjectBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class KanbanProjectPublic(KanbanProjectBase):
    id: uuid.UUID
    created_at: datetime | None = None


class KanbanProjectsPublic(SQLModel):
    data: list[KanbanProjectPublic]
    count: int


class KanbanBoardBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)


class KanbanBoardCreate(KanbanBoardBase):
    project_id: uuid.UUID


class KanbanBoardUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


class KanbanBoard(KanbanBoardBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="kanbanproject.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class KanbanBoardPublic(KanbanBoardBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime | None = None


class KanbanColumnKey(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class KanbanColumnBase(SQLModel):
    key: KanbanColumnKey
    title: str = Field(min_length=1, max_length=255)
    position: int = Field(default=0, ge=0)


class KanbanColumnCreate(KanbanColumnBase):
    board_id: uuid.UUID


class KanbanColumnUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]
    position: int | None = Field(default=None, ge=0)


class KanbanColumn(KanbanColumnBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    board_id: uuid.UUID = Field(
        foreign_key="kanbanboard.id", nullable=False, ondelete="CASCADE"
    )
    key: KanbanColumnKey = Field(sa_type=SAEnum(KanbanColumnKey))


class KanbanColumnPublic(KanbanColumnBase):
    id: uuid.UUID
    board_id: uuid.UUID


class KanbanTaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class KanbanTaskPrStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class KanbanTaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    priority: KanbanTaskPriority = Field(default=KanbanTaskPriority.MEDIUM)
    position: int = Field(default=0, ge=0)
    due_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    repo_full_name: str | None = Field(default=None, max_length=255)
    branch_name: str | None = Field(default=None, max_length=255)
    pr_number: int | None = Field(default=None, ge=1)
    pr_url: str | None = Field(default=None, max_length=1024)
    pr_status: KanbanTaskPrStatus | None = Field(default=None)
    last_commit_sha: str | None = Field(default=None, min_length=7, max_length=64)


class KanbanTaskCreate(KanbanTaskBase):
    board_id: uuid.UUID
    column_id: uuid.UUID


class KanbanTaskUpdate(SQLModel):
    column_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]
    description: str | None = Field(default=None, max_length=2000)
    priority: KanbanTaskPriority | None = None
    position: int | None = Field(default=None, ge=0)
    due_date: datetime | None = None
    repo_full_name: str | None = Field(default=None, max_length=255)
    branch_name: str | None = Field(default=None, max_length=255)
    pr_number: int | None = Field(default=None, ge=1)
    pr_url: str | None = Field(default=None, max_length=1024)
    pr_status: KanbanTaskPrStatus | None = None
    last_commit_sha: str | None = Field(default=None, min_length=7, max_length=64)


class KanbanTask(KanbanTaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    board_id: uuid.UUID = Field(
        foreign_key="kanbanboard.id", nullable=False, ondelete="CASCADE"
    )
    column_id: uuid.UUID = Field(
        foreign_key="kanbancolumn.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class KanbanTaskPublic(KanbanTaskBase):
    id: uuid.UUID
    board_id: uuid.UUID
    column_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KanbanTasksPublic(SQLModel):
    data: list[KanbanTaskPublic]
    count: int
