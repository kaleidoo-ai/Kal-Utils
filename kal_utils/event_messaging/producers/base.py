from abc import ABC, abstractmethod

# For Unittest
import unittest

class KalSenseBaseProducer(ABC):
    def __init__(self, topic: str, producer_group: str, exchange_type: str = "direct") -> None:
        super().__init__()
        self.__topic = topic
        self.__producer_group = producer_group
        self.__exchange_type = exchange_type
        self.__producer = None

    @property
    def exchange_type(self) -> str:
        return self.__exchange_type
    
    @exchange_type.setter
    def exchange_type(self, value: str):
        raise ValueError("Exchange type cannot be changed once set")
    
    @property
    def topic(self) -> str:
        return self.__topic
    
    @topic.setter
    def topic(self, value: str):
        raise ValueError("Topic cannot be changed once set, to change topics receive a new instance from the retriever class")
    
    @topic.deleter
    def topic(self):
        raise AttributeError("Topic cannot be deleted once set, entire instance should be created anew")
    
    @property
    def producer_group(self) -> str:
        return self.__producer_group
    
    @producer_group.setter
    def producer_group(self, value: str):
        raise ValueError("Producer group cannot be changed once set, to change producer_group receive a new instance from the retriever class")
    
    @producer_group.deleter
    def producer_group(self):
        raise AttributeError("Producer group cannot be deleted once set, entire instance should be created anew")
    
    @property
    def producer(self):
        raise AttributeError("Cannot access self.producer attribute, to produce to topic call obj.produce() instead")
    
    @producer.setter
    def producer(self, value):
        raise ValueError("Producer cannot be changed once set, to change producer receive a new instance from the retriever class")
    
    @producer.deleter
    def producer(self):
        raise AttributeError("Producer cannot be deleted once set, entire instance should be created anew")
            
    @abstractmethod
    def produce(self):
        pass
    
    @abstractmethod
    def __del__(self):
        pass


# ------------------------------------------- UNIT TEST -------------------------------------------

# Unittest
class TestKalSenseBaseProducer(unittest.TestCase):
    def test_abstract_class(self):
        with self.assertRaises(TypeError):
            KalSenseBaseProducer()
    
    def test_produce_method(self):
        class ConcreteProducer(KalSenseBaseProducer):
            def consume(self ,message):
                return message
        
        producer = ConcreteProducer()
        message = "Produced"
        self.assertEqual(producer.produce(message), "Produced")

if __name__ == '__main__':
    unittest.main()