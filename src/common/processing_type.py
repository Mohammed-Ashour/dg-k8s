from enum import Enum

class ProcessingType(Enum):
    realtime = "realtime"
    reprocessing = "reprocessing"
    
    def __str__(self):
        return self.value