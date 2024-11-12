from abc import ABC, abstractmethod
# from dotenv import load_dotenv
import os


# load environment variables
# load_dotenv()

class BaseProducerRetriever(ABC):
    def __init__(self):
        pass
    
    @classmethod
    @abstractmethod
    def get_producer():
        pass