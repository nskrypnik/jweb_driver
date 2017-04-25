from urllib.parse import urlparse
from functools import reduce


def _normalise_url(url):
    '''Remove hanging slash sign from url
    '''
    if url[-1] == '/':
        return url[:-1]
    return url


def are_urls_equal(url1, url2):
    '''Compare two urls and return True if equal
    '''
    url1 = urlparse(_normalise_url(url1))
    url2 = urlparse(_normalise_url(url2))

    return all(map(
        lambda key: getattr(url1, key) == getattr(url2, key),
        ['scheme', 'netloc', 'path', 'query']
    ))
