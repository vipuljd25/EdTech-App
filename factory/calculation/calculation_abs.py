import abc


class CalculationsAbs(abc.ABC):
    def __init__(self, student_id, **kwargs):
        self.collection = None
        self.set_collection()
        self.student_id = student_id
        self.kwargs = kwargs
        self.results = None

    @abc.abstractmethod
    def set_collection(self):
        raise NotImplementedError

    @abc.abstractmethod
    def is_calculation_in_timeframe(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_timeframe(self):
        raise NotImplementedError

    @abc.abstractmethod
    def calculate(self):
        raise NotImplementedError

