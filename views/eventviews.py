# Event-related views

from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from django.views import View

import tracker.horaro as horaro

__all__ = [
    'HoraroScheduleColsView',
]


class HoraroScheduleColsView(View):
    def get(self, request, slug):
        try:
            data = horaro.get_schedule_data(slug)
        except Exception as e:
            return HttpResponseServerError("Error getting schedule - {}".format(e))
        else:
            if not data:
                return HttpResponseNotFound("No schedule found")
            return JsonResponse(data[0]['columns'], safe=False)
