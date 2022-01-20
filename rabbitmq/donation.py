from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
import django.core.serializers as serializers
from django.db.models import Sum
from tracker.models.donation import Donation
import tracker.filters as filters

import pika
import json
import logging

log = logging.getLogger(__name__)

@receiver(signals.post_save, sender=Donation)
def RabbitDonationUpdate(sender, instance, created, **kwargs):
  if not settings.USE_AMQP:
    return
  parameters = pika.URLParameters(settings.AMQP_CONNECTIONSTRING)
  connection = pika.BlockingConnection(parameters)
  channel = connection.channel()

  send_donation_update_event(instance, created, channel)
  if instance.transactionstate == 'COMPLETED':
    send_update_totals_event(instance, channel)

def send_donation_update_event(instance, created, channel):
    data = {
      'event': instance.event.short,
      'id': instance.id,
      'time_received': str(instance.timereceived),
      'comment': instance.comment,
      'amount': instance.amount,
      'transactionstate': instance.transactionstate,
      'readstate': instance.readstate,
      'bidstate': instance.bidstate,
      'comment_state': instance.commentstate,
      'donor': {
        'id': instance.donor.id,
        'displayname': instance.donor.visible_name(),
        'email': instance.donor.email,
        'twitchusername': instance.twitchusername,
      },
      'donor_visiblename': instance.donor.visible_name(),
      'donor_email': instance.donor.email,
    }

    routing_key = instance.event.short + '.donation.' + str(instance.id) + donationState(instance, created)
    json_data = json.dumps(data, ensure_ascii=False, cls=serializers.json.DjangoJSONEncoder).encode('utf-8')
    
    log.debug("===== "+ routing_key + "=====")
    log.debug(json_data)
    log.debug("==========")
    
    channel.basic_publish(
      'tracker', 
      routing_key, 
      json_data, 
      pika.BasicProperties(
        content_type='application/json', 
        delivery_mode=2))

def send_update_totals_event(instance, channel):
    # Only emit totals change if transaction is completed.
    agg = filters.run_model_query('donation', {'event': instance.event.id }).aggregate(amount=Sum('amount'))
    aggregate_data = {
      'message_type': 'donation_total_change',
      'event': instance.event.short,
      'amount': instance.amount,
      'new_total': agg['amount'],
      'id': instance.id
    }
    routing_key = instance.event.short + '.donation_total.updated'
    json_data = json.dumps(aggregate_data, ensure_ascii=False, cls=serializers.json.DjangoJSONEncoder).encode('utf-8')
    
    log.debug("===== "+ routing_key + "=====")
    log.debug(json_data)
    log.debug("==========")

    channel.basic_publish(
      'tracker',
      routing_key,
      json_data,
      pika.BasicProperties(
        content_type='application/json', 
        delivery_mode=2))

def donationState(donation, created):
  if created:
    return ".created"

  return ".changed"