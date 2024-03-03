from inspect import getmembers, isclass, isabstract
import nudges.nudges_factory.nudges as nudges
from .nudges_abs import NudgesAbs


class NudgesFactory:
    """
    TODO send signals when Challenge Accept(consider challenge expiry)
    TODO notification limit
    TODO add notification in sql table
    """
    def __init__(self, student_id, action, **kwargs):
        self.action = action
        self.student_id = student_id
        self.kwargs = kwargs

        self.nudges = {}
        self.load_nudges()

        self.nudges_instance = self.create_instance()

    def load_nudges(self):
        notification_classes = getmembers(nudges, lambda m: isclass(m) and not isabstract(m))
        for name, _type in notification_classes:
            if isclass(_type) and issubclass(_type, NudgesAbs):
                self.nudges.update({name: _type})

    def create_instance(self):
        if self.action in self.nudges:
            return self.nudges[self.action](self.student_id, self.action, **self.kwargs)
        else:
            raise NotImplementedError
