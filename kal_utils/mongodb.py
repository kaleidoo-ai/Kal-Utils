from bson import ObjectId
from mongoengine import Document, ReferenceField, EmbeddedDocument

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
