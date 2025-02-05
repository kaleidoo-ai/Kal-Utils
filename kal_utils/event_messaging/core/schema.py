from enum import Enum
import pydantic
from pydantic import BaseModel, Field, field_validator, UUID4
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from kal_utils.mongodb import ValidObjectId
from kal_utils.event_messaging.core.constants import ErrorMessages, TranscriptionConstants

class Metadata(BaseModel):
    """
    Represents metadata associated with a message.
    
    Attributes:
        system (str): Source system identifier
        service (str): Generating service name
        timestamp (datetime): Message creation time
    """
    system: str = Field(..., example="analytics_service")
    service: str = Field(..., example="data_processing")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('timestamp')
    def validate_timestamp(cls, value):
        if value > datetime.now(timezone.utc):
            raise ValueError("Timestamp cannot be in the future")
        return value

    class Config:
        extra = "forbid"  # Prevent extra fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Message(BaseModel):
    """
    Represents a validated message in the system.
    
    Attributes:
        id (UUID4): Unique message identifier
        target (str): Message destination identifier
        source (str): Message origin identifier
        data (Dict): Payload content
        metadata (Metadata): System metadata
    """
    id: UUID4 = Field(..., description="RFC 4122-compliant UUID")
    target: str = Field(..., min_length=3, example="data_warehouse")
    source: str = Field(..., min_length=3, example="mobile_app")
    data: Dict[str, Any] = Field(..., example={"event": "user_action"})
    metadata: Metadata

    @field_validator('id')
    def validate_id(cls, value):
        return value

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "target": "data_warehouse",
                "source": "mobile_app",
                "data": {"key": "value"},
                "metadata": {
                    "system": "analytics",
                    "service": "processing",
                    "timestamp": "2023-10-01T12:00:00Z"
                }
            }
        }


# class Metadata(pydantic.BaseModel):
#     """
#     Represents metadata associated with a message.
    
#     Attributes:
#         system (str): The system from which the message originates.
#         service (str): The service that generated the message.
#         timestamp (str): The timestamp of when the message was created.
#     """
#     system: str
#     service: str
#     timestamp: str
    
#     class Config:
#         extra = "allow"
#         from_attributes = True
       
# class Message(pydantic.BaseModel):
#     """
#     Represents a message in the system.
    
#     Attributes:
#         id (str): The unique identifier of the message.
#         target (str): The target of the message.
#         source (str): The source of the message.
#         data (Dict): The data payload of the message.
#         metadata (Metadata): The metadata associated with the message.
#     """
#     id: str
#     target: str
#     source: str
#     data: Dict
#     metadata: Metadata
    
#     class Config:
#         extra = "forbid"
#         from_attributes = True