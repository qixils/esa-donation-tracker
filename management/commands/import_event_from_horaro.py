from django.core.management.base import BaseCommand, CommandError

import settings

import tracker.models as models
import tracker.horaro as horaro
import tracker.commandutil as commandutil

class Command(commandutil.TrackerCommand):
    help = 'Import event from horaro'

    def add_arguments(self, parser):
        parser.add_argument('-he', '--horaro', help='name of horaro event to import', required=False, default="esa/2018-winter")
        parser.add_argument('-e', '--event', help='name of event to import to', required=False, default="")

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        event = None
        try:
            event = models.Event.objects.get(short=options["event"])
        except models.Event.DoesNotExist:
            event = models.event.LatestEvent()

        horaro_id = event.horaro_name or options["horaro"]

        columns = horaro.Columns()
        horaro.UpdateSchedule(event, horaro_id, columns)