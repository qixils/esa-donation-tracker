from decimal import Decimal
import pytz
import json
import datetime
import random
import traceback
import requests

from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse,Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache, cache_page
from django.core import serializers
from django.core.urlresolvers import reverse
from django.conf import settings

import post_office.mail

from . import common as views_common
import tracker.models as models
import tracker.forms as forms
import tracker.viewutil as viewutil
import tracker.filters as filters
import tracker.paypalutil as paypalutil

__all__ = [
  'paypal_cancel',
  'paypal_return',
  'donate',
  'ipn',
  ]

@csrf_exempt
def paypal_cancel(request):
  return views_common.tracker_response(request, "tracker/paypal_cancel.html")

@csrf_exempt
def paypal_return(request, event):
  events = models.Event.objects.filter(short=event)
  if events.count() > 0:
    event = events[0]
  else:
    event = None

  if not event or event.locked or event.paypalreturntext == None:
    return views_common.tracker_response(request, "tracker/paypal_return_generic.html")
  return views_common.tracker_response(request, "tracker/paypal_return.html", {'event': event })

@csrf_exempt
@cache_page(300)
def donate(request, event):
  event = viewutil.get_event(event)
  if event.locked:
    return views_common.tracker_response(request, "tracker/donate_locked.html", {'event': event })
  bidsFormPrefix = "bidsform"
  prizeFormPrefix = "prizeForm"
  if request.method == 'POST':
    commentform = forms.DonationEntryForm(event=event,data=request.POST)
    if commentform.is_valid():
      prizesform = forms.PrizeTicketFormSet(amount=commentform.cleaned_data['amount'], data=request.POST, prefix=prizeFormPrefix)
      bidsform = forms.DonationBidFormSet(amount=commentform.cleaned_data['amount'], data=request.POST, prefix=bidsFormPrefix)
      if bidsform.is_valid() and prizesform.is_valid():
        with transaction.atomic():
          donation = models.Donation(amount=commentform.cleaned_data['amount'], timereceived=pytz.utc.localize(datetime.datetime.utcnow()), domain='PAYPAL', domainId=str(random.getrandbits(128)), event=event, testdonation=event.usepaypalsandbox)
          if commentform.cleaned_data['comment']:
            donation.comment = commentform.cleaned_data['comment']
            donation.commentstate = "PENDING"
          donation.requestedvisibility = commentform.cleaned_data['requestedvisibility']
          donation.requestedalias = commentform.cleaned_data['requestedalias']
          donation.requestedemail = commentform.cleaned_data['requestedemail']
          donation.requestedsolicitemail = commentform.cleaned_data['requestedsolicitemail']
          if 'twitchusername' in commentform.cleaned_data and commentform.cleaned_data['twitchusername']:
            donation.twitchusername = commentform.cleaned_data['twitchusername']
          donation.currency = event.paypalcurrency
          donation.save()
          for bidform in bidsform:
            if 'bid' in bidform.cleaned_data and bidform.cleaned_data['bid']:
              bid = bidform.cleaned_data['bid']
              if bid.allowuseroptions:
                # unfortunately, you can't use get_or_create when using a non-atomic transaction
                # this does technically introduce a race condition, I'm just going to hope that two people don't
                # suggest the same option at the exact same time
                # also, I want to do case-insensitive comparison on the name
                try:
                  bid = models.Bid.objects.get(event=bid.event, speedrun=bid.speedrun, name__iexact=bidform.cleaned_data['customoptionname'], parent=bid)
                except models.Bid.DoesNotExist:
                  bid = models.Bid.objects.create(event=bid.event, speedrun=bid.speedrun, name=bidform.cleaned_data['customoptionname'], parent=bid, state='PENDING', istarget=True)
              donation.bids.add(models.DonationBid(bid=bid, amount=Decimal(bidform.cleaned_data['amount'])), bulk=False)
          for prizeform in prizesform:
            if 'prize' in prizeform.cleaned_data and prizeform.cleaned_data['prize']:
              prize = prizeform.cleaned_data['prize']
              donation.tickets.add(models.PrizeTicket(prize=prize, amount=Decimal(prizeform.cleaned_data['amount'])))
          donation.full_clean()
          donation.save()

        serverURL = viewutil.get_request_server_url(request)
        paypalURL = settings.PAYPAL_DOMAIN.rstrip('/')

        paypal_dict = {
          "amount": str(donation.amount),
          "cmd": "_donations",
          "business": donation.event.paypalemail,
          "item_name": donation.event.receivername,
          "notify_url": paypalURL + reverse('tracker:ipn'),
          "return_url": serverURL + reverse('tracker:paypal_return', kwargs={'event': event.short}),
          "cancel_return": serverURL + reverse('tracker:paypal_cancel'),
          "custom": str(donation.id) + ":" + donation.domainId,
          "currency_code": donation.event.paypalcurrency,
          "no_shipping": 0,
        }

        # Create the form instance
        form = forms.PayPalDonationsForm(button_type="donate", sandbox=donation.event.usepaypalsandbox, initial=paypal_dict)
        context = {"event": donation.event, "form": form }
        return views_common.tracker_response(request, "tracker/paypal_redirect.html", context)
    else:
      bidsform = forms.DonationBidFormSet(amount=Decimal('0.00'), data=request.POST, prefix=bidsFormPrefix)
      prizesform = forms.PrizeTicketFormSet(amount=Decimal('0.00'), data=request.POST, prefix=prizeFormPrefix)
  else:
    commentform = forms.DonationEntryForm(event=event)
    bidsform = forms.DonationBidFormSet(amount=Decimal('0.00'), prefix=bidsFormPrefix)
    prizesform = forms.PrizeTicketFormSet(amount=Decimal('0.00'), prefix=prizeFormPrefix)

  def bid_parent_info(bid):
    if bid != None:
      return {'name': bid.name, 'description': bid.description, 'parent': bid_parent_info(bid.parent) }
    else:
      return None

  def bid_info(bid):
    result = {
      'id': bid.id,
      'name': bid.name,
      'description': bid.description,
      'label': bid.full_label(not bid.allowuseroptions),
      'count': bid.count,
      'amount': bid.total,
      'goal': Decimal(bid.goal or '0.00'),
      'parent': bid_parent_info(bid.parent)
    }
    if bid.speedrun:
      result['runname'] = bid.speedrun.name
    if bid.suggestions.exists():
      result['suggested'] = list(map(lambda x: x.name, bid.suggestions.all()))
    if bid.allowuseroptions:
      result['custom'] = ['custom']
      result['label'] += ' (select and add a name next to "New Option Name")'
    return result

  bids = filters.run_model_query('bidtarget', {'state':'OPENED', 'event':event.id }, user=request.user).distinct().select_related('parent').prefetch_related('suggestions')

  allPrizes = filters.run_model_query('prize', {'feed': 'current', 'event': event.id })

  prizes = allPrizes.filter(ticketdraw=False)

  dumpArray = [bid_info(o) for o in bids]

  bidsJson = json.dumps(dumpArray, ensure_ascii=False, cls=serializers.json.DjangoJSONEncoder)

  ticketPrizes = allPrizes.filter(ticketdraw=True)

  def prize_info(prize):
    result = {'id': prize.id, 'name': prize.name, 'description': prize.description, 'minimumbid': prize.minimumbid, 'maximumbid': prize.maximumbid, 'sumdonations': prize.sumdonations}
    return result

  dumpArray = [prize_info(o) for o in ticketPrizes.all()]
  ticketPrizesJson = json.dumps(dumpArray, ensure_ascii=False, cls=serializers.json.DjangoJSONEncoder)
  page_settings = { 
    'organization': settings.SITE_NAME_SHORT
  }

  return views_common.tracker_response(request, "tracker/donate.html", {
    'settings': page_settings,
    'event': event, 
    'bidsform': bidsform, 
    'prizesform': prizesform, 
    'commentform': commentform, 
    'hasBids': bids.count() > 0, 
    'bidsJson': bidsJson, 
    'hasTicketPrizes': ticketPrizes.count() > 0, 
    'ticketPrizesJson': ticketPrizesJson, 
    'prizes': prizes
    })

@csrf_exempt
@never_cache
def ipn(request):
  ipnObj = None

  if request.method == 'GET' or len(request.POST) == 0:
    return views_common.tracker_response(request, "tracker/badobject.html", {})

  try:
    ipnObj = paypalutil.create_ipn(request)
    ipnObj.save()

    donation = paypalutil.initialize_paypal_donation(ipnObj)
    donation.save()

    if donation.transactionstate == 'PENDING':
      reasonExplanation, ourFault = paypalutil.get_pending_reason_details(ipnObj.pending_reason)
      if donation.event.pendingdonationemailtemplate:
        formatContext = {
          'event': donation.event,
          'donation': donation,
          'donor': donation.donor,
          'pending_reason': ipnObj.pending_reason,
          'reason_info': reasonExplanation if not ourFault else '',
        }
        post_office.mail.send(recipients=[donation.donor.email], sender=donation.event.donationemailsender, template=donation.event.pendingdonationemailtemplate, context=formatContext)
      # some pending reasons can be a problem with the receiver account, we should keep track of them
      if ourFault:
        paypalutil.log_ipn(ipnObj, 'Unhandled pending error')
    elif donation.transactionstate == 'COMPLETED':
      if donation.event.donationemailtemplate != None:
        formatContext = {
          'donation': donation,
          'donor': donation.donor,
          'event': donation.event,
          'prizes': viewutil.get_donation_prize_info(donation),
        }
        post_office.mail.send(recipients=[donation.donor.email], sender=donation.event.donationemailsender, template=donation.event.donationemailtemplate, context=formatContext)

      agg = filters.run_model_query('donation', {'event': donation.event.id }).aggregate(amount=Sum('amount'))

      # When a donation's PayPal transaction completes, output a postback.
      postbackData = {
        'message_type': 'donation_total_change',
        'event': donation.event.short,
        'amount': donation.amount,
        'new_total': agg['amount'],
        'id': donation.id
      }
      postbackJSon = json.dumps(postbackData, ensure_ascii=False, cls=serializers.json.DjangoJSONEncoder).encode('utf-8')
      postbacks = models.PostbackURL.objects.filter(event=donation.event)
      for postback in postbacks:
        requests.post(postback.url, data=postbackJSon, headers={'Content-Type': 'application/json; charset=utf-8'})
    elif donation.transactionstate == 'CANCELLED':
      # eventually we may want to send out e-mail for some of the possible cases
      # such as payment reversal due to double-transactions (this has happened before)
      paypalutil.log_ipn(ipnObj, 'Cancelled/reversed payment')

  except Exception as inst:
    # just to make sure we have a record of it somewhere
    print("ERROR IN IPN RESPONSE, FIX IT")
    if ipnObj:
      paypalutil.log_ipn(ipnObj, "{0} \n {1}. POST data : {2}".format(inst, traceback.format_exc(inst), request.POST))
    else:
      viewutil.tracker_log('paypal', 'IPN creation failed: {0} \n {1}. POST data : {2}'.format(inst, traceback.format_exc(inst), request.POST))
  return HttpResponse("OKAY")
