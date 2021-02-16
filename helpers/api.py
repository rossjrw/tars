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

with open(pathlib.Path.cwd() / "keys.secret.toml") as keys:
    keys = tomlkit.parse(keys.read())['keys']

GOOGLE_CSE_API_KEY = keys['google_cse_api']
GOOGLE_CSE_ID = keys['google_cse_id']
NICKSERV_PASSWORD = keys['irc_password']


def toml_url(url):
    """Grab a TOML file from URL and return the parsed object"""
    response = requests.get(url)
    return tomlkit.parse(response.text)


class CromAPI:
    """Wrapper for Crom API functions."""

    page_graphql = """
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
    """

    def __init__(self, domain):
        self.endpoint = "https://api.crom.avn.sh/"
        self.domain = {'en': "http://scp-wiki.wikidot.com"}[domain]

    def _get(self, query):
        return requests.post(
            self.endpoint,
            json={'query': query.replace("@domain", self.domain)},
        )

    def _get_one_page(self, slug):
        """Gets all Crom data for a single page."""
        response = self._get(
            f"""{{
                page (
                    url: "@domain/{slug}"
                ) {{
                    {CromAPI.page_graphql}
                }}
            }}"""
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
        if tags is not None or categories is not None:
            raise NotImplementedError
        date_filter = (
            ""
            if seconds is None
            else f"""
                wikidotInfo: {{
                    createdAt: {{
                        gte: "{pd.now().subtract(seconds=seconds).isoformat()}"
                    }}
                }}
            """
        )

        def paginated_generator():
            previous_end_cursor = ""
            while True:
                response = self._get(
                    f"""{{
                        pages (
                            sort: {{
                                order: DESC
                                key: CREATED_AT
                            }}
                            filter: {{
                                anyBaseUrl: "@domain"
                                {date_filter}
                            }}
                            first: 100
                            after: "{previous_end_cursor}"
                        ) {{
                            edges {{
                                node {{
                                    {CromAPI.page_graphql}
                                }}
                            }}
                            pageInfo {{
                                hasNextPage
                                endCursor
                            }}
                        }}
                    }}"""
                )
                data = json.loads(response.text)['data']['pages']
                yield [
                    self._process_page_data(edge['node'])
                    for edge in data['edges']
                ]
                if not data['pageInfo']['hasNextPage']:
                    return
                previous_end_cursor = data['pageInfo']['endCursor']

        return paginated_generator()


SCPWiki = CromAPI("en")
