from tars.helpers.api import CromAPI


def test_crom_api():
    """Simple test cases for the Crom API wrapper."""
    api = CromAPI("en")

    # Honestly, the tag list seems like the only thing that I'm reasonably guaranteeing
    # won't be screwed with in the future.
    scp_5000 = api.get_one_page_meta("scp-5000")
    assert 'scp' in scp_5000['tags']

    oldest_pages_iterator = api.get_all_pages()

    oldest_pages_1 = next(oldest_pages_iterator)
    assert len(oldest_pages_1) == 100
    assert oldest_pages_1[0]['title'] == 'Manage Site'

    oldest_pages_2 = next(oldest_pages_iterator)
    assert len(oldest_pages_2) == 100
    assert oldest_pages_2[0]['title'] == 'SCP-145'

    oldest_tales = next(api.get_all_pages(tags=['tale']))
    assert oldest_tales[0]['title'] == 'Archived Incident 076-2_682'

    nav_pages = next(api.get_all_pages(categories=['nav']))
    assert len(nav_pages) == 2
    assert nav_pages[0]['title'] == 'Top Bar Menu'
    assert nav_pages[1]['title'] == 'Side'
