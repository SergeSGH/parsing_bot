# import requests
from urllib.request import urlopen

from lxml import etree


def site_av_price(url, xpath):
    response = urlopen(url)
    htmlparser = etree.HTMLParser()
    tree = etree.parse(response, htmlparser)
    price_data = tree.xpath(xpath)
    prices = []
    for price in price_data:
        price_clean = ''.join([s for s in price if s.isdigit()])
        if price_clean:
            prices.append(int(price_clean))
    if prices:
        return str(round(sum(prices) / len(prices), 1))
    return 'нет данных'
