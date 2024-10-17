from typing import TypeVar, Generic, Union

DataType = TypeVar("DataType")
ErrorTypes = TypeVar("ErrorTypes", bound=Exception)

class Result(Generic[DataType, ErrorTypes]):
    def __init__(self, data: Union[DataType, None] = None, error: Union[ErrorTypes, None] = None):
        self.data = data
        self.error = error

    def unwrap(self) -> DataType:
        if self.error:
            raise self.error
        if self.data is None:
            raise ValueError("No data available")
        return self.data

def build(data: DataType = None, error: ErrorTypes = None) -> Result[DataType, ErrorTypes]:
    return Result(data=data, error=error)
