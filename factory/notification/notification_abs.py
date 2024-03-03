import abc


class NotificationAbs(abc.ABC):
    def __init__(self, platform, **kwargs):
        self.platform = platform
        self.kwargs = kwargs

    # @abc.abstractmethod
    # def send_notification(self, heading, content, image_url, device_token_list, data, in_app=True):
    #     return NotImplementedError
