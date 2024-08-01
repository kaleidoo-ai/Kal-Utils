import re
from bson import ObjectId
from bson.errors import InvalidId
from mongoengine import Document, ReferenceField, EmbeddedDocument

class ValidObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not isinstance(v, str):
            raise ValueError('Invalid ObjectId: must be a string')

        try:
            ObjectId(v)
        except InvalidId:
            raise ValueError('Invalid ObjectId format')

        return v


class ValidDomain(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not isinstance(v, str):
            raise ValueError('Domain must be a string')

        # Regular expression for domain validation
        domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        )

        if not domain_regex.match(v):
            raise ValueError('Invalid domain format')

        return v

def mongo_to_dict(obj):
    if not obj:
        return None
    data = {}
    for field_name, field_value in obj._fields.items():
        value = getattr(obj, field_name)

        # Check if the value is a reference field
        if isinstance(field_value, ReferenceField):
            # If it's a ReferenceField, store only the ObjectId as a string
            referenced_object = getattr(obj, field_name)
            data[field_name] = str(referenced_object.id) if referenced_object else None
        elif isinstance(value, ObjectId):
            # Convert ObjectId to string
            data[field_name] = str(value)
        elif isinstance(value, EmbeddedDocument):
            # Recursively handle embedded documents
            data[field_name] = mongo_to_dict(value)
        elif isinstance(value, list):
            # Handle lists, potentially of embedded documents or ReferenceFields
            data[field_name] = [mongo_to_dict(item) if isinstance(item, Document) else item for item in value]
        else:
            # Assign all other data types directly
            data[field_name] = value
    return data
