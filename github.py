from time import sleep, time
from collections import namedtuple

import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter, Retry

Repository = namedtuple('Repository', 'owner name')


class GitHubRetry(Retry):
    def increment(self, method, url, response=None, error=None, _pool=None, _stacktrace=None):
        if response and response.status in {403, 429}:
            rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
            wait_until_reset = max(0, int(rate_limit_reset - time()) + 1)
            sleep(wait_until_reset)
        return super().increment(method, url, response, error, _pool, _stacktrace)


class GitHubAPIError(Exception):
    pass


class GitHubAPI:

    def __init__(self, api_token, api_url: str = 'https://api.github.com/', timeout: int = 180):
        self.api_url = api_url
        self.timeout = timeout
        retries = GitHubRetry(total=10,
                              backoff_factor=2,
                              status_forcelist=(403, 429, 500, 501, 502, 503, 504,),
                              raise_on_status=True)
        self.http_session = Session()
        self.http_session.headers.update({
            'User-Agent': 'GithubAPI/1.0',
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {api_token}',
        })
        http_adapter = HTTPAdapter(max_retries=retries)
        self.http_session.mount('https://', http_adapter)
        self.http_session.mount('http://', http_adapter)

    def query(self, endpoint: str, params: dict = {}, paginate=True):
        response = self.http_session.get(self.api_url + endpoint, timeout=self.timeout, params=params)
        result = response.json()

        while 'next' in response.links and paginate:
            next_url = response.links['next']['url']
            response = self.http_session.get(next_url, timeout=self.timeout)
            result += response.json()

        return result


def get_login(user_dict):
    if user_dict:
        return user_dict.get('login')
    return None


def extract_activities(pulls, timelines):
    events = []
    for pull in pulls:
        pull_number = pull['number']
        login = get_login(pull['user'])
        events += [(login, pull['created_at'], 'created', pull_number)]

        for event in timelines[pull['number']]:
            event_type = event['event']
            match event_type:
                case 'reviewed':
                    login = get_login(event.get('user'))
                    events += [(login, event['submitted_at'],
                                event_type, pull_number)]
                case 'commit-commented' | 'line-commented':
                    for comment in event['comments']:
                        login = get_login(comment.get('user'))
                        events += [(login, comment['updated_at'],
                                    event_type, pull_number)]
                case 'created' | 'closed' | 'commented' | 'reopened':
                    login = get_login(event.get('actor'))
                    events += [(login, event['created_at'],
                                event_type, pull_number)]
                case _:
                    pass

    activities = pd.DataFrame(events, columns=['user_id', 'timestamp', 'action', 'pr_id']).drop_duplicates()
    activities.timestamp = pd.to_datetime(activities.timestamp).dt.tz_localize(None)
    activities.pr_id = activities.pr_id.astype(str)
    return activities
