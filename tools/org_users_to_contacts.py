"""
DEPENDENCIES:
pip3 install requests

USAGE:
python3 tools/org_users_to_contacts.py --outfile ~/Desktop/contacts.csv
"""
import os
import argparse

import requests


HEADER = """Name,Given Name,Additional Name,Family Name,Yomi Name,Given Name Yomi,Additional Name Yomi,Family Name Yomi,Name Prefix,Name Suffix,Initials,Nickname,Short Name,Maiden Name,Birthday,Gender,Location,Billing Information,Directory Server,Mileage,Occupation,Hobby,Sensitivity,Priority,Subject,Notes,Group Membership,E-mail 1 - Type,E-mail 1 - Value,E-mail 2 - Type,E-mail 2 - Value,E-mail 3 - Type,E-mail 3 - Value,Phone 1 - Type,Phone 1 - Value,Phone 2 - Type,Phone 2 - Value,Address 1 - Type,Address 1 - Formatted,Address 1 - Street,Address 1 - City,Address 1 - PO Box,Address 1 - Region,Address 1 - Postal Code,Address 1 - Country,Address 1 - Extended Address,Address 2 - Type,Address 2 - Formatted,Address 2 - Street,Address 2 - City,Address 2 - PO Box,Address 2 - Region,Address 2 - Postal Code,Address 2 - Country,Address 2 - Extended Address,Organization 1 - Type,Organization 1 - Name,Organization 1 - Yomi Name,Organization 1 - Title,Organization 1 - Department,Organization 1 - Symbol,Organization 1 - Location,Organization 1 - Job Description,Website 1 - Type,Website 1 - Value,Website 2 - Type,Website 2 - Value
"""

LINE_TEMPLATE = '{},{},,{},,,,,,,,,,,,,,,,,,,,,,,Brigada Organization Users,* ,{},,,,,,,,,,,,,,,,,,,,,,,,,,,,{},,,,,,,,,,'


class TokenAuth:
    def __init__(self, auth_prefix, token):
        self.auth_prefix = auth_prefix  # e.g. 'Bearer'
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = '{0} {1}'.format(self.auth_prefix, self.token).strip()
        return r


def get_contact_lines(token):
    BASE_URL = 'https://api.brigada.mx/api/'
    r = requests.get(f'{BASE_URL}internal/organization_users/', auth=TokenAuth('Bearer', token), timeout=15)
    r.raise_for_status()
    lines = [LINE_TEMPLATE.format(
        u['full_name'], u['first_name'], u['surnames'], u['email'], u['organization']['name']
    ) for u in r.json()['results']]
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key_file', default='.secret-key')
    parser.add_argument('-o', '--outfile', default='org_user_google_contacts.csv')

    args = parser.parse_args()
    with open(os.path.expanduser(args.key_file), 'r') as file:
        key = file.readline().strip()

    with open(os.path.expanduser(args.outfile), 'w') as file:
        file.write(f'{HEADER}{get_contact_lines(key)}\n')
