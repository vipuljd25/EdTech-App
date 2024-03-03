from inspect import getmembers, isclass, isabstract
import factory.challenge.sub_challenges as sub_challenges
from factory.challenge.base_challenge import BaseChallenge
from factory.challenge.challenge_abs import ChallengeAbs


class ChallengeFactory:
    def __init__(self, action, student_id, **kwargs):
        self.action = action
        self.student_id = student_id
        self.kwargs = kwargs
        self.sub_challenge = {}
        self.load_challenges()
        self.challenge_instance = self.create_instance()
        self.challenge_instance.check_challenge_completed()

    def load_challenges(self):
        challenge_classes = getmembers(sub_challenges, lambda m: isclass(m) and not isabstract(m))
        for name, _type in challenge_classes:
            if isclass(_type) and issubclass(_type, ChallengeAbs):
                self.sub_challenge.update({name: _type})

    def create_instance(self):
        if self.action in self.sub_challenge:
            return self.sub_challenge[self.action](self.action, self.student_id, **self.kwargs)
        else:
            return BaseChallenge(self.action, self.student_id, **self.kwargs)

