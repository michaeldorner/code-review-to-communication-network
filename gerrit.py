import json
from datetime import datetime

import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from tqdm.auto import tqdm


class GerritAPI:
    JSON_OFFET = len("]}\\\'\n")
    GERRIT_PARAMS = [
        ('o', 'DETAILED_ACCOUNTS'),
        ('o', 'SKIP_DIFFSTAT'),
        #    ('o', 'REVIEWER_UPDATES'),
        #    ('o', 'ALL_REVISIONS'),
        ('o', 'MESSAGES'),
        #    ('o', 'DETAILED_LABELS'),
    ]

    def __init__(self, url):
        self.url = url
        self.http_session = Session()
        self.http_session.headers.update({
            'User-Agent': 'GerritAPI/1.0',
            'Accept': 'application/json',
        })

        retries = Retry(
            total=10,
            backoff_factor=2,
            status_forcelist={413, 429, 503},
        )
        http_adapter = HTTPAdapter(max_retries=retries)
        self.http_session.mount("http://", http_adapter)
        self.http_session.mount("https://", http_adapter)

    def query(self, endpoint) -> list[str]:
        last_change = {'_more_changes': True}
        before = datetime.now()
        skip = 0
        changes = []

        while '_more_changes' in last_change:
            before_str = str(before)
            response = self.http_session.get(f'{self.url}/{endpoint}/', timeout=10 * 60, params=GerritAPI.GERRIT_PARAMS + [('q', f'before:"{before_str}"'), ('S', skip)])
            if response.status_code == 200:
                new_changes = json.loads(response.text[GerritAPI.JSON_OFFET:])
                assert isinstance(new_changes, list), 'Parsed response is not a list'
                changes += new_changes
            else:
                print(f'Error with {response.url}')
            first_change = new_changes[0]
            last_change = new_changes[-1]

            first_change_timestamp = datetime.fromisoformat(first_change['updated'])
            last_change_timestamp = datetime.fromisoformat(last_change['updated'])

            if first_change_timestamp != last_change_timestamp:
                before = last_change_timestamp
                skip = 0
            else:
                skip += len(new_changes)

            print(f'Downloaded {len(new_changes)} changes between {first_change_timestamp} and {last_change_timestamp} (S={skip})')
        return changes


def extract_activities(changes: list) -> pd.DataFrame:
    events = []
    anonymous_messages = []
    for change in tqdm(changes):
        change_id = change['id']
        for message in change['messages']:
            author = message.get('author')
            if author and 'tags' not in author:  # exclude all SERVICE_USERS

                # remove all unnecessary fields from author
                for k in ('display_name', 'status', 'inactive'):
                    author.pop(k, None)

                event = {
                    'change_id': change_id,
                    'timestamp': message['date'],
                    'message': message['message'],
                    'message_tag': message.get('tag')
                } | author
                events += [event]
            else:
                anonymous_messages += [message]

    activities = pd.DataFrame(events)
    activities.timestamp = pd.to_datetime(activities.timestamp)

    return activities
