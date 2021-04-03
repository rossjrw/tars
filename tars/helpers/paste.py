import requests


def paste(text):
    """
    Pastes a Markdown string to rentry.co.
    Returns the URL of the paste.
    """
    session = requests.session()
    token = session.get("https://rentry.co").cookies['csrftoken']
    response = session.post(
        "https://rentry.co/api/new",
        data={'text': text, 'csrfmiddlewaretoken': token},
        headers={'Referer': "https://rentry.co"},
    )
    return response.json()['url']
