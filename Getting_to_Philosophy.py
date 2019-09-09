import sys
import time

import requests
import urllib.parse

import lxml.html as lh


class LoopException(Exception):
    pass


class InvalidPageNameError(Exception):
    pass


class LinkNotFoundError(Exception):
    pass


def strip_parentheses(string):
    """
    Remove parentheses from a string
    """
    nested_parentheses = nesting_level = 0
    result = ''
    for c in string:
        if nested_parentheses < 1:
            if c == '<':
                nesting_level += 1
            if c == '>':
                nesting_level -= 1

        if nesting_level < 1:
            if c == '(':
                nested_parentheses += 1
            if nested_parentheses < 1:
                result += c
            if c == ')':
                nested_parentheses -= 1

        else:
            result += c

    return result


visited = []


def trace(page=None, end='Philosophy', whole_page=False):
    """
    Visit the first non-italicized, not-within-parentheses
        link of page recursively until the page 'Philosophy' is reached.

    """

    time.sleep(0.5)

    BASE_URL = 'https://en.wikipedia.org/w/api.php'
    HEADERS = {'User-Agent': 'Firefox/1.0.0'}

    params = {
        'action': 'parse',
        'page': page,
        'prop': 'text',
        'format': 'json',
        'redirects': 1
    }

    if not whole_page:
        params['section'] = 0

    result = requests.get(BASE_URL, params=params, headers=HEADERS).json()

    page = result['parse']['title']

    if page in visited:
        yield page
        del visited[:]
        raise LoopException('Loop detected')

    if not whole_page:
        yield page

    if page == end:
        del visited[:]
        return

    raw_html = result['parse']['text']['*']
    html = lh.fromstring(raw_html)

    for elm in html.cssselect('.reference,span,div,.thumb,'
                              'table,a.new,i,#coordinates'):
        elm.drop_tree()

    html = lh.fromstring(strip_parentheses(lh.tostring(html).decode('utf-8')))
    link_found = False
    for elm, attr, link, pos in html.iterlinks():
        if attr != 'href':
            continue
        next_page = link

        if not next_page.startswith('/wiki/'):
            continue

        next_page = next_page[len('/wiki/'):]
        next_page = urllib.parse.unquote(next_page)

        next_page = next_page.replace('_', ' ')

        pos = next_page.find('#')
        if pos != -1:
            next_page = next_page[:pos]

        link_found = True
        visited.append(page)

        for m in trace(page=next_page, end=end, whole_page=whole_page):
            yield m

        break

    if not link_found:
        if whole_page:
            del visited[:]
            raise LinkNotFoundError(
                'No valid link found in page "{0}"'.format(page)
            )
        else:
            for m in trace(page=page, whole_page=True, end=end):
                yield m


def process(names, times=1):
    raised = False

    try:
        link_count = -1
        for s in names:
            if s == end:
                s = s.replace(" ", "_")
                print("http://en.wikipedia.org/wiki/" + s)
            else:
                s = s.replace(" ", "_")
                print("http://en.wikipedia.org/wiki/" + s)
            link_count += 1



    except LoopException as e:
        print('---\n{}, quitting...'.format(e))
        raised = True

    except InvalidPageNameError as e:
        print(e)
        raised = True

    except LinkNotFoundError as e:
        print(e)
        print('---')
        print('could not find appropriate link in last link')
        raised = True

    if not raised:
        print('---')
        print('Number of Links visited: {}'.format(
            link_count,
            ))

    if times == times:
        return

    print()

    names = trace(end=end)
    process(names, times=times + 1)


if __name__ == '__main__':

    urlRandom = 'http://en.wikipedia.org/wiki/Special:Random'

    if len(sys.argv) == 1:
        print("Start from http://en.wikipedia.org/wiki/Special:Random")
        url = urlRandom
    else:
        url = sys.argv[1]

    result = requests.get(url)

    pagename = result.url.split("/")[-1]
    # pagename="Computer"

    end = 'Philosophy'
    names = trace(page=pagename, end='Philosophy')
    process(names)
