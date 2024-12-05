from typing import TypeVar, Generic, Union, Optional

DataType = TypeVar("DataType")
ErrorTypes = TypeVar("ErrorTypes", bound=Exception)

class Result(Generic[DataType, ErrorTypes]):
    def __init__(self, data: Optional[DataType] = None, error: Optional[ErrorTypes] = None):
        if error is not None and not isinstance(error, Exception):
            raise TypeError("Error must be an instance of Exception or a subclass of it.")
        if data is None and error is None:
            raise ValueError("Either data or error must be provided.")
        self.data = data
        self.error = error

    def is_ok(self) -> bool:
        return self.error is None

    def is_error(self) -> bool:
        return self.error is not None

    def unwrap(self) -> DataType:
        if self.error:
            raise self.error
        if self.data is None:
            raise ValueError("Result has no data.")
        return self.data

def build(data: Optional[DataType] = None, error: Optional[ErrorTypes] = None) -> Result[DataType, ErrorTypes]:
    if error is not None and not isinstance(error, Exception):
        raise TypeError("Error must be an instance of Exception or a subclass of it.")
    return Result(data=data, error=error)
