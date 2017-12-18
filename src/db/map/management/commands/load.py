"""
USAGE:
python manage.py load --load_dir db/load
python manage.py load --locality_csv db/load/<locality_csv>
"""
import os
import csv

from django.core.management.base import BaseCommand

from helpers.location import geos_location_from_coordinates
from db.map.models import Locality, Municipality, State


def load_locality(row):
    """Load locality row from sheet to DB.
    """
    cvegeo_state, state_name, cvegeo_municipality, municipality_name, cvegeo_locality, name, \
        latitude, longitude, elevation, *rest = row
    cvegeo_state = cvegeo_state.strip()
    cvegeo_municipality = cvegeo_state + cvegeo_municipality.strip()
    cvegeo = cvegeo_municipality + cvegeo_locality.strip()

    locality = Locality.objects.filter(cvegeo=cvegeo).first()
    if locality is None:
        Locality.objects.create(
            cvegeo=cvegeo, name=name,
            cvegeo_municipality=cvegeo_municipality, municipality_name=municipality_name,
            cvegeo_state=cvegeo_state, state_name=state_name,
            location=geos_location_from_coordinates(float(latitude), float(longitude)),
            elevation=float(elevation),
        )


def load_municipality(row):
    """Load municipality row from sheet to DB.
    """
    cvegeo_state, state_name, cvegeo_municipality, municipality_name, *rest = row
    cvegeo_state = cvegeo_state.strip()
    cvegeo_municipality = cvegeo_state + cvegeo_municipality.strip()

    municipality = Municipality.objects.filter(cvegeo_municipality=cvegeo_municipality).first()
    if municipality is None:
        Municipality.objects.create(
            cvegeo_municipality=cvegeo_municipality, municipality_name=municipality_name,
            cvegeo_state=cvegeo_state, state_name=state_name,
        )


def load_state(row):
    """Load state row from sheet to DB.
    """
    cvegeo_state, state_name, *rest = row
    cvegeo_state = cvegeo_state.strip()

    state = State.objects.filter(cvegeo_state=cvegeo_state).first()
    if state is None:
        State.objects.create(cvegeo_state=cvegeo_state, state_name=state_name)


def load_from_csv(csv_file, entity):
    """Get geographical entities from flat file and insert them into DB.
    """
    entity_loader = {
        'locality': load_locality,
        'municipality': load_municipality,
        'state': load_state,
    }
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, lineterminator='\n')
        next(reader, None)
        for row in reader:
            entity_loader[entity](row)


def sync_locality_features(csv_file):
    return


class Command(BaseCommand):
    help = 'Loads or syncs certain DB tables from CSV files'

    def add_arguments(self, parser):
        parser.add_argument('--locality_csv', help='File to update existing locality records')
        parser.add_argument('--load_dir', help='Directory to load loc, state and muni records')

    def handle(self, *args, **options):
        locality_csv = options.get('locality_csv')
        load_dir = options.get('load_dir')
        if load_dir is not None:
            print('loading localities, municipalities and states')
            for entity in ['locality', 'municipality', 'state']:
                csv_file = os.path.join(load_dir, '{}.csv'.format(entity))
                load_from_csv(csv_file, entity)

        if locality_csv is not None:
            print('syncing locality features')
            csv_file = args[1]
            sync_locality_features(locality_csv)
