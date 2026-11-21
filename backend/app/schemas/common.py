"""Common reusable API schemas."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Standard generic API response."""

    success: bool = Field(default=True, description="Whether the operation succeeded")
    message: str = Field(description="Informational message")
    data: Optional[Any] = Field(default=None, description="Response payload")


class ErrorResponse(BaseModel):
    """Standard error response structure."""

    detail: str = Field(description="Human-readable error explanation")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error identifier")

