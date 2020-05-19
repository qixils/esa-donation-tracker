from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings

from rest_framework.renderers import JSONRenderer

from tracker.api.serializers import DonationSerializer
from tracker.models.donation import Donation

import pika
import json

@receiver(signals.post_save, sender=Donation)
def RabbitDonationUpdate(sender, instance, **kwargs):
  if settings.USE_AMQP:
    parameters = pika.URLParameters(settings.AMQP_CONNECTIONSTRING)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    serializer = DonationSerializer(instance)
    json_data = JSONRenderer().render(serializer.data)
    channel.basic_publish('tracker', 'donation.change', json_data, pika.BasicProperties(content_type='application/json', delivery_mode=2))