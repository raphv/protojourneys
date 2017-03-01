from __future__ import unicode_literals

import re
import json
from django.conf import settings
from django.utils.html import format_html
from django.utils.text import Truncator
from lxml import etree
try: #python 2.7
    from StringIO import StringIO
    from urllib import urlencode
    from urllib2 import urlopen, HTTPError, Request
    from urlparse import urljoin, urlparse
except ImportError: #python 3.4
    from io import StringIO
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode, urljoin, urlparse
    from urllib.error import HTTPError


providers = [
    {
        'name': 'Dailymotion',
        'patterns': [
            r'^https?://www\.dailymotion\.com/video/',
        ],
        'endpoint': 'http://www.dailymotion.com/services/oembed',
    },
    {
        'name': 'Flickr',
        'patterns': [
            r'^https?://(?:www\.)?flickr\.com/',
            r'^https?://flic\.kr/',
        ],
        'endpoint': 'http://www.flickr.com/services/oembed/',
        'additional_get_params': {
            'format': 'json',
        },
    },
    {
        'name': 'Instagram',
        'patterns': [
            r'^https?://(?:www\.)?instagr(?:\.am|am\.com)/',
        ],
        'endpoint': 'http://api.instagram.com/oembed',
    },
    {
        'name': 'Soundcloud',
        'patterns': [
            r'^https?://soundcloud\.com/',
        ],
        'endpoint': 'https://soundcloud.com/oembed',
        'additional_get_params': {
            'format': 'json',
        },
    },
    {
        'name': 'Vimeo',
        'patterns': [
            r'^https?://(?:www\.)?vimeo\.com/',
        ],
        'endpoint': 'http://www.vimeo.com/api/oembed.json',
    },
    {
        'name': 'Wordpress.com',
        'patterns': [
            r'^https?://(?:[^/]+\.)?wordpress\.com/',
            r'^https?://wp\.me/',
            r'^https?://(?:[^/]+\.)?videopress\.com/',
            
        ],
        'endpoint': 'http://public-api.wordpress.com/oembed/',
        'additional_get_params': {
            'for': 'protojourneys',
        },
    },
    {
        'name': 'Youtube',
        'patterns': [
            r'^https?://(?:www\.)?youtube\.com/watch',
            r'^https?://youtu\.be/',
        ],
        'endpoint': 'https://www.youtube.com/oembed/',
    }
]

def get_oembed_from_url(json_url):
    print("Loading data from %s"%json_url)
    try:
        res = urlopen(json_url)
        data = res.read()
        json_data = json.loads(data)
        if 'error' in json_data:
            raise Exception("oEmbed provider error %s"%json_data['error'])
        return json_data
    except HTTPError as e:
        contents = e.read()
        msg = "oEmbed provider error (HTTP %d) %s"%(
            e.code, Truncator(contents or '').chars(80)
        )
        print(msg)
        raise Exception(msg)
    except ValueError:
        print("Value Error %s"%e.message)
        raise Exception("oEmbed provider returned invalid JSON: %s"%data)
    except Exception as e:
        print("Other exception %s"%e.message)
        raise e

def get_oembed_from_provider(provider, url):
    dict = {
        'url': url,
        'width': 480,
    }
    if 'additional_get_params' in provider:
        for param in provider['additional_get_params']:
            dict[param] = provider['additional_get_params'][param]
    params = urlencode(dict)
    json_url = '%s?%s'%(provider['endpoint'],params)
    return get_oembed_from_url(json_url)

def get_oembed_from_provider_list(provider_list, url):
    for provider in provider_list:
        print("Trying patterns from %s"%provider['name'])
        for pattern in provider['patterns']:
            if re.match(pattern, url):
                return get_oembed_from_provider(provider, url)
    print('No matching provider')
    raise Exception("No oEmbed provider for URL")

xpath_mappings = [
    ('//*[@itemprop="description"][1]/@content','description'),
    ('//*[@itemprop="image"][1]/@content','thumbnail_url'),
    ('//title[1]/text()','title'),
    ('//meta[@name="description"][1]/@content','description'),
    ('//meta[@property="og:title"][1]/@content','title'),
    ('//meta[@property="og:description"][1]/@content','description'),
    ('//meta[@property="og:image"][1]/@content','thumbnail_url'),
    ('//meta[@property="og:image:width"][1]/@content','thumbnail_width'),
    ('//meta[@property="og:image:height"][1]/@content','thumbnail_height'),
]

def get_oembed(url):
    if not re.match('^https?://', url):
        raise Exception("Error: URL must start with http:// or https://")
    try:
        return get_oembed_from_provider_list(providers, url)
    except Exception:
        try:
            req = Request(
                url,
                None,
                {
                    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0",
                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    'Accept-Language': "en-GB,en;q=0.5",
                    'Referer': 'https://www.google.co.uk',
                    'Host': urlparse(url).hostname,
                }
            )
            urlres = urlopen(req)
            html = urlres.read()
            tree = etree.parse(StringIO(html),etree.HTMLParser())
            oembedurl = tree.xpath('//link[@type="application/json+oembed"][1]/@href')
            if oembedurl:
                print("URL provides their own oEmbed endpoint")
                return get_oembed_from_url(oembedurl[0])
            res = {}
            for path, prop in xpath_mappings:
                xpathres = tree.xpath(path)
                if xpathres:
                    res[prop] = "%s"%(xpathres[0])
            headers = [h.split(':',1)[0].lower() for h in urlres.info().headers]
            if 'x-frame-options' in headers:
                print("iframe not allowed")
            else:
                res['html'] = format_html(
                    '<iframe width="{}" height="{}" src="{}"></iframe>',
                    '100%',
                    '320',
                    url
                )
                res['provider_name'] = 'iframe'
            if 'thumbnail_url' in res:
                res['thumbnail_url'] = urljoin(url, res['thumbnail_url'])
            return res
        except HTTPError as e:
            contents = e.read()
            msg = "Error while retrieving page URL (HTTP %d) %s"%(
                e.code,
                Truncator(contents or '').chars(80)
            )
            print(msg)
            raise Exception(msg)
        except Exception as e:
            print("Other exception %s"%e.message)
            raise e
        