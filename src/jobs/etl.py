import os
import re
from dateutil.parser import parse

from django.db import transaction

import pygsheets
from celery import shared_task

from db.map.models import Locality, Organization, Action, ActionLog
from db.choices import ORGANIZATION_SECTOR_CHOICES


def parse_or_none(parser, s):
    """Parse `s` with `parser`. Return `None` if exception is raised.
    """
    try:
        return parser(s)
    except:
        return None


def sync_organization(row):
    (key, name, desc, year_established, rfc, sector, person_responsible, phone, email, website,
        street, city, zip_code, *rest) = [v.strip() for v in row]

    organization = Organization.objects.filter(key=key).first()
    if organization is None:
        organization = Organization(key=key)

    if sector not in [c[0] for c in ORGANIZATION_SECTOR_CHOICES]:
        sector = 'civil'

    year_established = parse_or_none(int, year_established)

    fields = {
        'name': name,
        'desc': desc,
        'year_established': year_established,
        'sector': sector,
        'contact': {
            'person_responsible': person_responsible,
            'phone': phone,
            'email': email,
            'website': website,
            'address': {
                'street': street,
                'city': 'Ciudad de México',
                'zip': zip_code,
            },
        }
    }
    organization.update_fields(**fields)
    try:
        organization.save()
    except:
        return None
    else:
        return organization


def sync_action(row, organization):
    """Sync action row from sheet with DB. New `ActionLog`s are only created if
    action changed since last read.
    """
    (key, locality_s, action_type, desc, target, unit_of_measurement, progress, budget,
        start_date, end_date, published, *rest) = [v.strip() for v in row]

    cvegeo = locality_s.strip().split('(')[-1][:-1].strip()
    if not cvegeo or not key:
        return

    locality = Locality.objects.filter(cvegeo=cvegeo).first()
    if locality is None or not desc:
        return

    def date_parse(s):
        return parse(s).date()

    def money_parse(s):
        """Deals with strings of this form: `$195.000,00`.
        """
        if len(s) >= 3 and (s[-3] == ',' or s[-3] == '.'):
            s = s[:-3]
        return float(re.sub('[^\d]', '', s))

    start_date = parse_or_none(date_parse, start_date)
    end_date = parse_or_none(date_parse, end_date)
    target = parse_or_none(float, target)
    budget = parse_or_none(money_parse, budget)
    progress = parse_or_none(float, progress)
    published = published.strip().lower() != 'no'

    fields = {
        'locality': locality,
        'action_type': action_type,
        'desc': desc,
        'target': target,
        'unit_of_measurement': unit_of_measurement,
        'progress': progress,
        'budget': budget,
        'start_date': start_date,
        'end_date': end_date,
        'published': published,
    }

    key = int(key)
    action = organization.action_set.filter(key=key).first()
    if action is None:
        action = Action.objects.create(
            key=key, organization=organization, source='google_sheets', **fields)
        ActionLog.objects.create(action=action, **fields)
        return

    if any(getattr(action, k) != v for k, v in fields.items()):
        action.update_fields(**fields) # only create new `ActionLog` object if fields have changed
        ActionLog.objects.create(action=action, **fields)


def get_google_client():
    from django.conf import settings
    file = os.path.join(settings.HOME, 'client_secret.json')
    return pygsheets.authorize(service_file=file)


@shared_task(name='etl_actions')
def etl_actions():
    """Get actions from Google sheet and insert them into DB.
    """
    client = get_google_client()
    sheets = client.open_by_url(
        'https://docs.google.com/spreadsheets/d/1vantwWHd55hNYC5nnNRo8uf9wp8yXRNOMFUY2a5ZPtA'
    )

    action_sheets = [s for s in sheets if s.title.startswith('_')]
    for sheet in action_sheets:
        rows = sheet.get_all_values()

        organization = sync_organization(rows[1])
        if not organization:
            return

        for row in rows[3:]:
            with transaction.atomic():
                sync_action(row, organization)
