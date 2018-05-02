# Tiltify functionality for loading donation info using their API.

import logging
import re

import requests
from django.core.exceptions import ValidationError
from django.utils import dateparse

from tracker.models import Donor, Donation

CAMPAIGN_URL = 'https://tiltify.com/api/v2/campaign'
DONATIONS_URL = 'https://tiltify.com/api/v2/campaign/donations'

logger = logging.getLogger(__name__)


def _get_tiltify_data(url, api_key):
    headers = {
        'Authorization': 'Token token="{}"'.format(api_key),
    }
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        logger.error("Error getting URL {0!r} - {1}".format(url, r.status_code))
        raise requests.exceptions.HTTPError(r.status_code)

    data = r.json()
    return data


def _parse_tiltify_datetime(val):
    """Parse a datetime value from the Tiltify API response.  The time zone offset has an extra space before it so we
    need to alter the incoming value slightly in order for Django to be able to parse it.
    """
    ts = re.sub(r'\s*([-+]?)(\d{2})(\d{2})$', r'\1\2:\3', val)
    return dateparse.parse_datetime(ts)


def get_campaign_data(api_key):
    """Get campaign data for the given Tiltify API key.

    :param api_key: API key of the campaign to retrieve.
    :type api_key: str
    :return: Donation data object.
    :rtype: dict
    """
    return _get_tiltify_data(CAMPAIGN_URL, api_key)


def get_donation_data(api_key):
    """Get donations for the given Tiltify API key.

    :param api_key: API key of the campaign to retrieve.
    :type api_key: str
    :return: List of donations.
    :rtype: list[dict]
    """
    return _get_tiltify_data(DONATIONS_URL, api_key)


def sync_event_donations(event):
    """Sync donations from a Tiltify campaign with an event in our system.

    :param event: Event record to merge.
    :type event: tracker.models.Event
    :return: Number of donations updated.
    :rtype: int
    """
    if not event.tiltify_api_key:
        raise ValidationError("API key not set")

    # Get campaign data to update start date for event.
    t_campaign = get_campaign_data(event.tiltify_api_key)

    start = dateparse.parse_date(t_campaign['starts'])
    if start:
        event.date = start

    event.save()

    # Get donations from Tiltify API.
    t_donations = get_donation_data(event.tiltify_api_key)
    num_donations = 0

    for t_donation in t_donations:
        # Get donor based on alias.
        donor = None
        if t_donation['name'] and t_donation['name'] != 'Anonymous':
            try:
                donor = Donor.objects.get(alias__iexact=t_donation['name'])
            except Donor.DoesNotExist:
                donor = Donor(email=t_donation['name'], alias=t_donation['name'])
                donor.save()

        # Get donation based on payment reference.
        try:
            donation = Donation.objects.select_for_update().get(domain='TILTIFY', domainId=t_donation['id'])
        except Donation.DoesNotExist:
            donation = Donation(event=event, domain='TILTIFY', domainId=t_donation['id'], readstate='PENDING',
                                commentstate='PENDING', donor=donor)

        # Make sure this donation wasn't already imported for a different event.
        if donation.event != event:
            raise ValidationError("Donation {!r} already exists for a different event".format(donation.domainId))

        donation.transactionstate = 'COMPLETED'
        donation.amount = t_donation['amount']
        donation.currency = t_donation['currency_code']
        donation.timereceived = _parse_tiltify_datetime(t_donation['created'])
        donation.testdonation = event.usepaypalsandbox

        # Comment might be null from Tiltify, but can't be null on our end.
        if t_donation['comment']:
            donation.comment = t_donation['comment']
        else:
            donation.comment = ''

        donation.save()
        num_donations += 1

    return num_donations
