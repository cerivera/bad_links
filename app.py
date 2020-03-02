from http import HTTPStatus
from concurrent import futures
from requests.exceptions import ConnectionError
import re

import requests

MAX_WORKERS = 20

class BadSourceUrl(Exception):
    pass

def find_bad_links_slow(url):
    urls = find_urls_in_content(get_content_from_url(url))
    return [url for url in urls if is_link_bad(url)[0]]

def find_bad_links_fast(url):
    urls = find_urls_in_content(get_content_from_url(url))
    num_workers = min(MAX_WORKERS, len(urls))
    with futures.ThreadPoolExecutor(num_workers) as executor:
        responses = executor.map(is_link_bad, urls)

    return [url for (is_bad, url) in responses if is_bad]


def is_link_bad(url):
    print("Checking {}".format(url))
    try:
        resp = requests.get(url)
        return (not resp.ok, url)
    except ConnectionError:
        return (True, url)

def get_content_from_url(url):
    resp = requests.get(url)
    if not resp.ok:
        raise BadSourceUrl(resp.status_code)

    return resp.content.decode('utf-8')

def find_urls_in_content(content):
    urls = set()
    # TODO support relative URLs
    single_quote_pattern = re.compile(r"href='(http[^']+)'")
    double_quote_pattern = re.compile(r'href="(http[^"]+)"')

    for url in re.findall(single_quote_pattern, content):
        urls.add(url)

    for url in re.findall(double_quote_pattern, content):
        urls.add(url)

    return urls

