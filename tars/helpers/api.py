"""api.py

Provides methods for accessing API.

API keys should be kept in keys.secret.toml in the base directory. This is a
TOML file containing a single table named 'keys' containing each key with its
value as a string.

The keys are:
    irc_password: The bots' IRC NickServ password.
    google_cse_api: The API key for the mismatch search via Google CSE.
    google_cse_id: The ID of the Google CSE.
    scuttle_api: A Personal Access Token for SCUTTLE.
"""

import json
import pathlib

import tomlkit
import requests
import pendulum as pd

keyfile = pathlib.Path.cwd() / "config/keys.secret.toml"

if keyfile.exists():
    with open(keyfile) as keys:
        keys = tomlkit.parse(keys.read())['keys']
else:
    print("No secret keyfile; some things will not work")
    keys = {}

GOOGLE_CSE_API_KEY = keys.get('google_cse_api', None)
GOOGLE_CSE_ID = keys.get('google_cse_id', None)
NICKSERV_PASSWORD = keys.get('irc_password', None)


def toml_url(url):
    """Grab a TOML file from URL and return the parsed object"""
    response = requests.get(url)
    return tomlkit.parse(response.text)


class CromAPI:
    """Wrapper for Crom API functions."""

    page_fragment_graphql = """
        fragment PageFragment on Page {
            url
            attributions {
                type
                user {
                    name
                }
                date
            }
            alternateTitles {
                type
                title
            }
            wikidotInfo {
                title
                category
                rating
                voteCount
                tags
                createdAt
                parent {
                    url
                }
            }
        }
    """

    get_one_page_query = """
        query GetOnePage($url: URL!) {
            page (url: $url) {
                ...PageFragment
            }
        }
    """

    get_all_pages_query = """
        query GetAllPages($filter: QueryPagesFilter!, $after: ID) {
            pages (
                filter: $filter
                first: 100
                after: $after
                sort: { order: ASC, key: CREATED_AT }
            ) {
                edges {
                    node {
                        ...PageFragment
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    def __init__(self, domain):
        self.endpoint = "https://api.crom.avn.sh/"
        self.domain = {'en': "http://scp-wiki.wikidot.com"}[domain]

    def _get(self, query, variables={}):
        return requests.post(
            self.endpoint,
            json={'query': query, 'variables': variables},
        )

    def _get_one_page(self, slug):
        """Gets all Crom data for a single page."""
        response = self._get(
            self.page_fragment_graphql + self.get_one_page_query,
            {'url': f"{self.domain}/{slug}"},
        )
        return json.loads(response.text)['data']['page']

    def _process_page_data(self, page_data):
        """Converts page data structure from Crom to TARS."""
        wd_metadata = page_data['wikidotInfo']
        metadata = {
            'tags': wd_metadata['tags'],
            'title': wd_metadata['title'],
            'rating': wd_metadata['rating'],
            'fullname': page_data['url'].split("/")[-1],
            'created_at': wd_metadata['createdAt'],
            'created_by': [
                attribution['user']['name']
                for attribution in page_data['attributions']
                if attribution['type'] in ["SUBMITTER", "AUTHOR"]
            ],
            'parent_fullname': (
                None
                if wd_metadata['parent'] is None
                else wd_metadata['parent']['url'].split("/")[-1]
            ),
        }
        if len(page_data['alternateTitles']) > 0:
            meta_titles = filter(
                lambda alt: alt['type'] == self.domain,
                page_data['alternateTitles'],
            )
            try:
                metadata['meta_title'] = next(meta_titles)['title']
            except StopIteration:
                pass
        return metadata

    def get_one_page_meta(self, slug):
        """Gets Wikidot metadata for a single page."""
        return self._process_page_data(self._get_one_page(slug))

    def get_all_pages(self, *, tags=None, categories=None, seconds=None):
        """Returns a generator that gets data for all pages on the wiki."""

        # Generate a Crom filter expression based on the arguments.
        # Create references to elements inside the expression that we can
        # modify later.
        wikidot_info_filter = {'category': {'neq': 'fragment'}}
        tag_filters = []
        category_filters = []
        page_filter = {
            'url': {'startsWith': self.domain},
            'wikidotInfo': {
                '_and': [
                    wikidot_info_filter,
                    {'_or': tag_filters},
                    {'_or': category_filters},
                ]
            },
        }

        if seconds is not None:
            wikidot_info_filter['createdAt'] = {
                'gte': pd.now().subtract(seconds=seconds).isoformat()
            }
        if tags is not None:
            tag_filters.extend({'tags': {'eq': tag}} for tag in tags)
        if categories is not None:
            category_filters.extend(
                {'category': {'eq': category}} for category in categories
            )

        def paginated_generator():
            next_cursor = None
            while True:
                response = self._get(
                    self.page_fragment_graphql + self.get_all_pages_query,
                    {'filter': page_filter, 'after': next_cursor},
                )
                data = json.loads(response.text)['data']['pages']
                yield [
                    self._process_page_data(edge['node'])
                    for edge in data['edges']
                ]
                if not data['pageInfo']['hasNextPage']:
                    return
                next_cursor = data['pageInfo']['endCursor']

        return paginated_generator()


SCPWiki = CromAPI("en")
