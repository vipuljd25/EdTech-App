from inspect import getmembers, isclass, isabstract
import factory.notification.notification as notification
from factory.notification.notification_abs import NotificationAbs


class NotificationFactory:
    def __init__(self, platform, **kwargs):
        self.platform = platform
        self.kwargs = kwargs
        self.notification = {}
        self.load_notification()
        self.notification_instance = self.create_instance()

    def load_notification(self):
        notification_classes = getmembers(notification, lambda m: isclass(m) and not isabstract(m))
        for name, _type in notification_classes:
            if isclass(_type) and issubclass(_type, NotificationAbs):
                self.notification.update({name: _type})

    def create_instance(self):
        if self.platform in self.platform:
            return self.notification[self.platform](self.platform)
        else:
            raise NotImplementedError
