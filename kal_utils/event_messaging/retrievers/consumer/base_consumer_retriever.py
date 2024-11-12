from abc import ABC, abstractmethod
# from dotenv import load_dotenv
import os

# For unittests
import unittest

# load environment variables
# load_dotenv()

class BaseConsumerRetriever(ABC):
    def __init__(self):
        super().__init__()
        pass
    
    @classmethod
    @abstractmethod
    def get_consumer():
        pass


# ------------------------------------------- UNIT TEST -------------------------------------------

# Unittest
class TestBaseConsumerRetriever(unittest.TestCase):
    def test_abstract_class(self):
        with self.assertRaises(TypeError):
            BaseConsumerRetriever()
    
    def test_get_consumer_method(self):
        class ConcreteRetriever(BaseConsumerRetriever):
            @classmethod
            def get_consumer(cls):
                return "Consumer"
        
        self.assertEqual(ConcreteRetriever.get_consumer(), "Consumer")

if __name__ == '__main__':
    unittest.main()