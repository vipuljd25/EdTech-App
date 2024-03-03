from django.core.management.base import BaseCommand
from events.consumer import consume_sqs_messages


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        consume_sqs_messages()
