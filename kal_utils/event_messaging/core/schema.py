from enum import Enum
import pydantic
from pydantic import BaseModel, field_validator, Field, Extra
from typing import Optional, List, Dict, Any
from ...mongodb import ValidObjectId
from ...event_messaging.core.constants import ErrorMessages, TranscriptionConstants


    
class Metadata(pydantic.BaseModel):
    """
    Represents metadata associated with a message.
    
    Attributes:
        system (str): The system from which the message originates.
        service (str): The service that generated the message.
        timestamp (str): The timestamp of when the message was created.
    """
    system: str
    service: str
    timestamp: str
    
    class Config:
        extra = "allow"
        from_attributes = True
       
class Message(pydantic.BaseModel):
    """
    Represents a message in the system.
    
    Attributes:
        id (str): The unique identifier of the message.
        target (str): The target of the message.
        source (str): The source of the message.
        data (Dict): The data payload of the message.
        metadata (Metadata): The metadata associated with the message.
    """
    id: str
    target: str
    source: str
    data: Dict
    metadata: Metadata
    
    class Config:
        extra = "forbid"
        from_attributes = True