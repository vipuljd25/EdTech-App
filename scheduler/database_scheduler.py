from django_celery_beat import schedulers


class CustomDatabaseScheduler(schedulers.DatabaseScheduler):

    def all_as_schedule(self):
        s = {}
        for model in self.Model.objects.filter(enabled__in=[True]).prefetch_related(
            "interval", "crontab", "solar", "clocked"
        ):
            try:
                s[model.name] = self.Entry(model, app=self.app)
            except ValueError:
                pass
        return s
