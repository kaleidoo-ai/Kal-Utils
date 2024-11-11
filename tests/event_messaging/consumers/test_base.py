from abc import ABC

# For Unittest
import unittest

from consumers.base import KalSenseBaseConsumer

# ------------------------------------------- UNIT TEST -------------------------------------------

class TestKalSenseBaseConsumer(unittest.TestCase):
    def setUp(self):
        class ConcreteConsumer(KalSenseBaseConsumer):
            def consume(self):
                pass
            
            def __del__(self):
                pass
        
        self.consumer = ConcreteConsumer("test_topic", "test_group")

    def test_initialization(self):
        self.assertEqual(self.consumer.topic, "test_topic")
        self.assertEqual(self.consumer.consumer_group, "test_group")

    def test_topic_property(self):
        with self.assertRaises(ValueError):
            self.consumer.topic = "new_topic"
        
        with self.assertRaises(AttributeError):
            del self.consumer.topic

    def test_consumer_group_property(self):
        with self.assertRaises(ValueError):
            self.consumer.consumer_group = "new_group"
        
        with self.assertRaises(AttributeError):
            del self.consumer.consumer_group

    def test_consumer_property(self):
        with self.assertRaises(AttributeError):
            _ = self.consumer.consumer
        
        with self.assertRaises(ValueError):
            self.consumer.consumer = "new_consumer"
        
        with self.assertRaises(AttributeError):
            del self.consumer.consumer

    def test_abstract_methods(self):
        self.assertTrue(hasattr(self.consumer, 'consume'))
        self.assertTrue(hasattr(self.consumer, '__del__'))

if __name__ == '__main__':
    unittest.main()