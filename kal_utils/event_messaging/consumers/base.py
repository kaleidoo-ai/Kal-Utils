from abc import ABC, abstractmethod

class KalSenseBaseConsumer(ABC):
    def __init__(self, topic: str, consumer_group: str, exchange_type: str = "direct") -> None:
        super().__init__()
        self.__topic = topic
        self.__consumer_group = consumer_group
        self.__exchange_type = exchange_type
        self.__consumer = None
    
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
    def consumer_group(self) -> str:
        return self.__consumer_group
    
    @consumer_group.setter
    def consumer_group(self, value: str):
        raise ValueError("Consumer group cannot be changed once set, to change consumer_group receive a new instance from the retriever class")
    
    @consumer_group.deleter
    def consumer_group(self):
        raise AttributeError("Consumer group cannot be deleted once set, entire instance should be created anew")
    
    @property
    def consumer(self):
        raise AttributeError("Cannot access self.consumer attribute, to consume from topic call obj.consume() instead")
    
    @consumer.setter
    def consumer(self, value):
        raise ValueError("Consumer cannot be changed once set, to change consumer receive a new instance from the retriever class")
    
    @consumer.deleter
    def consumer(self):
        raise AttributeError("Consumer cannot be deleted once set, entire instance should be created anew")
    
    @abstractmethod
    def consume(self):
        pass
    
    @abstractmethod
    def __del__(self):
        pass