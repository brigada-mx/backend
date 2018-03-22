"""
DEPENDENCIES:
pip3 install requests

USAGE:
python3 tools/org_users_to_contacts.py
"""
import argparse

import requests


HEADER = """Name,Given Name,Additional Name,Family Name,Yomi Name,Given Name Yomi,Additional Name Yomi,Family Name Yomi,Name Prefix,Name Suffix,Initials,Nickname,Short Name,Maiden Name,Birthday,Gender,Location,Billing Information,Directory Server,Mileage,Occupation,Hobby,Sensitivity,Priority,Subject,Notes,Group Membership,E-mail 1 - Type,E-mail 1 - Value
"""

LINE_TEMPLATE = '{},{},,{},,,,,,,,,,,,,,,,,,,,,,,Brigada Organization Users,* ,{}'


class TokenAuth:
    def __init__(self, auth_prefix, token):
        self.auth_prefix = auth_prefix  # e.g. 'Bearer'
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = '{0} {1}'.format(self.auth_prefix, self.token).strip()
        return r


def get_contact_lines(token):
    r = requests.get('https://api.brigada.mx/api/internal/organization_users/', auth=TokenAuth('Bearer', token))
    r.raise_for_status()
    lines = [LINE_TEMPLATE.format(
        u['first_name'], u['surnames'], u['full_name'], u['email']
    ) for u in r.json()['results']]
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key_file', default='.secret-key')
    parser.add_argument('-o', '--outfile', default='org_user_google_contacts.csv')

    args = parser.parse_args()
    with open(args.key_file, 'r') as file:
        key = file.readline().strip()

    with open(args.outfile, 'w') as file:
        file.write(f'{HEADER}{get_contact_lines(key)}\n')
