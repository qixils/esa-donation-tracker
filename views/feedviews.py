# Views for the public data feed for our tickers.

from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic.base import View

from tracker import viewutil, filters


class UpcomingRunsView(View):
    def get(self, request, event, *args, **kwargs):
        # Get the next 3 upcoming runs for the event that haven't finished yet.
        event = viewutil.get_event(event)
        now = timezone.now()
        params = {
            'event': event.id,
            'endtime_gte': now,
        }
        runs = filters.run_model_query('run', params)[:3]

        results = []
        for run in runs:
            results.append({
                'game': run.name,
                'category': run.category,
                'estimate': str(run.run_time),
                'runners': [r.name for r in run.runners.all()],
            })

        return JsonResponse({'results': results})


class UpcomingBidsView(View):
    def get(self, request, event, *args, **kwargs):
        # Get the upcoming bids and their options + totals.
        event = viewutil.get_event(event)
        now = timezone.now()
        params = {
            'event': event.id,
            'state': 'OPENED',
        }
        bids = filters.run_model_query('bid', params).filter(speedrun__endtime__gte=now).select_related(
            'speedrun').prefetch_related('options')
        results = []

        for bid in bids:
            result = {
                'game': bid.speedrun.name,
                'bid': bid.name,
                'goal': bid.goal,
                'amount_raised': bid.total,
                'options': [],
            }
            for option in bid.options.all():
                result['options'].append({
                    'name': option.name,
                    'amount_raised': option.total,
                })
                result['amount_raised'] += option.total

            results.append(result)

        return JsonResponse({'results': results})


class CurrentDonationsView(View):
    def get(self, request, event, *args, **kwargs):
        event = viewutil.get_event(event)
        params = {
            'event': event.id,
        }
        agg = filters.run_model_query('donation', params).aggregate(amount=Coalesce(Sum('amount'), Decimal('0.00')))

        return JsonResponse({
            'total': agg['amount'],
        })

