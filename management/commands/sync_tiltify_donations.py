import requests
from django.core.exceptions import ValidationError
from django.db import transaction

import tracker.commandutil as commandutil
import tracker.models as models
import tracker.tiltify as tiltify
import tracker.viewutil as viewutil


class Command(commandutil.TrackerCommand):
    help = 'Import/sync Tiltify donations for events with Tiltify sync enabled'
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument('-e', '--event', help='specify an event for which event to sync donations',
                            type=viewutil.get_event)
        parser.add_argument('-d', '--dry-run', help='Run the command, but do not commit any changes to the database.',
                            action='store_true')

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        dry_run = options['dry_run']

        event_set = models.Event.objects.filter(tiltify_enable_sync=True, tiltify_api_key__isnull=False)

        if options['event']:
            event = viewutil.get_event(options['event'])
            event_set = event_set.filter(pk=event.id)

        try:
            with transaction.atomic():
                for event in event_set:
                    self.message('Syncing event #{0}...'.format(event.pk))
                    try:
                        num_donations = tiltify.sync_event_donations(event)
                    except (ValidationError, requests.exceptions.RequestException) as e:
                        self.message("Error syncing event #{} - {}".format(event.pk, e))
                        raise
                    else:
                        self.message('Synced {} donations.'.format(num_donations))

                if dry_run:
                    self.message("Rolling back operations...")
                    raise Exception("Cancelled due to dry run.")
        except:
            self.message("Rollback complete.")

        self.message("Completed.")
