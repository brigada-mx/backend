import os
import re
import csv
from dateutil.parser import parse

from django.db import transaction

import pygsheets
from celery import shared_task

from db.map.models import Locality, Organization, Action, ActionLog


def parse_or_none(parser, s):
    """Parse `s` with `parser`. Return `None` if exception is raised.
    """
    try:
        return parser(s)
    except:
        return None


def sync_action(row, sheet_title):
    """Sync action row from sheet with DB. New `ActionLog`s are only created if
    action changed since last read.
    """
    row_key, state, locality_s, sub_organization, action_type, desc, \
        long_desc, unit_of_measurement, target, budget, spent, start_date, \
        end_date, status, person_responsible, email, phone, *rest = [v.strip() for v in row]

    cvegeo = locality_s.strip().split('(')[-1][:-1].strip()
    if not cvegeo or not row_key:
        return

    locality = Locality.objects.filter(cvegeo=cvegeo).first()
    if locality is None or (not desc and not long_desc):
        return

    organization = Organization.objects.filter(key=sheet_title).first()
    if organization is None:
        organization = Organization.objects.create(key=sheet_title)

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
    spent = parse_or_none(money_parse, spent)
    contact = {
        'person_responsible': person_responsible,
        'email': email,
        'phone': phone,
    }

    fields = {
        'locality': locality,
        'sub_organization': sub_organization,
        'action_type': action_type,
        'desc': desc,
        'long_desc': long_desc,
        'unit_of_measurement': unit_of_measurement,
        'target': target,
        'budget': budget,
        'spent': spent,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'contact': contact
    }

    key = '{}|{}'.format(sheet_title, row_key)
    action = Action.objects.filter(key=key).first()
    if action is None:
        action = Action.objects.create(key=key, organization=organization,
                                       source='google_sheets', locality=locality)
        action.update_fields(**fields)
        ActionLog.objects.create(action=action, **fields)
        return

    for k, v in fields.items():  # only create new `ActionLog` object if fields have changed
        if getattr(action, k) == v:
            continue
        action.update_fields(**fields)
        ActionLog.objects.create(action=action, **fields)
        return


def sync_locality(row):
    """Sync locality row from sheet with DB.
    """
    state_name, municipality_name, name, cvegeo = row[:4]
    cvegeo = cvegeo.strip()
    if not cvegeo:
        return

    locality = Locality.objects.filter(cvegeo=cvegeo).first()
    if locality is None:
        Locality.objects.create(name=name, municipality_name=municipality_name,
                                state_name=state_name, cvegeo=cvegeo)


def get_google_client():
    from django.conf import settings
    file = os.path.join(settings.HOME, 'client_secret.json')
    return pygsheets.authorize(service_file=file)


@shared_task(name='etl_localities')
def etl_localities():
    """Get localities from Google sheet and insert them into DB.
    """
    from django.conf import settings
    client = get_google_client()
    sheets = client.open('Acciones 719S')

    sheet = sheets.worksheet_by_title('Geografias')
    csv_file = os.path.join(settings.HOME, 'localities.csv')
    sheet.export(pygsheets.ExportType.CSV, filename=csv_file)

    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, lineterminator='\n')
        next(reader, None)
        for row in reader:
            sync_locality(row)


@shared_task(name='etl_actions')
def etl_actions():
    """Get actions from Google sheet and insert them into DB.
    """
    client = get_google_client()
    sheets = client.open('Acciones 719S')

    action_sheets = [s for s in sheets if s.title.startswith('_')]
    for sheet in action_sheets:
        rows = sheet.get_all_values()

        for row in rows[1:]:
            with transaction.atomic():
                sync_action(row, sheet.title)
