from inspect import getmembers, isclass, isabstract
import factory.milestone.milestones as milestones
from factory.milestone.milestone_abs import MilestoneAbs
from factory.constance import MILESTONES


class MilestoneFactory:
    def __init__(self, action, student_id, **kwargs):
        self.action = MILESTONES[action]
        self.student_id = student_id
        self.kwargs = kwargs
        self.milestone = {}
        self.load_milestone()
        self.instance = self.create_instance()
        self.instance.process_milestone()

    def load_milestone(self):
        milestone_classes = getmembers(milestones, lambda m: isclass(m) and not isabstract(m))
        for name, _type in milestone_classes:
            if isclass(_type) and issubclass(_type, MilestoneAbs):
                self.milestone.update({name: _type})

    def create_instance(self):
        if self.action in self.milestone:
            return self.milestone[self.action](self.student_id, **self.kwargs)
        else:
            raise NotImplementedError
