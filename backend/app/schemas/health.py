"""Schemas for health-check and root endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Application health status response schema."""

    status: str = Field(default="healthy", description="Application health status")
    version: str = Field(description="API semantic version")
    service: str = Field(description="Service name")
    timestamp: datetime = Field(description="Current UTC timestamp")
    environment: str = Field(description="Current deployment environment")
    database: Optional[str] = Field(default=None, description="Database connection health status")


class RootResponse(BaseModel):
    """Root welcome endpoint response schema."""

    message: str = Field(description="Welcome message")
    status: str = Field(default="online", description="Service availability status")
    docs: Optional[str] = Field(default=None, description="Interactive documentation URL")
    redoc: Optional[str] = Field(default=None, description="ReDoc documentation URL")
    version: str = Field(description="API version")
    api_v1_prefix: str = Field(description="Prefix for version 1 API endpoints")
