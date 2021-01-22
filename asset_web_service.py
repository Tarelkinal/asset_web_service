"""
Web service to work with assets, get actual information about
daily currency rate and key indicators
"""
import logging.config
import requests

from flask import Flask, render_template, abort, jsonify, request
from lxml import etree
import yaml

from composite_store import AssetItem, CompositeAssetItem

API_ROUTE = '/api/asset'
APPLICATION_NAME = 'asset_web_service'
CBR_BASE_URL = 'https://www.cbr.ru/eng/'
CBR_CURRENCY_RATE_URL = f'{CBR_BASE_URL}currency_base/daily/'
CBR_KEY_INDICATORS_URL = f'{CBR_BASE_URL}key-indicators/'
JSON_DAILY_ROUTE = '/cbr/daily'
JSON_KEY_INDICATORS_ROUTE = '/cbr/key_indicators'
LOGGING_CONFIG_YAML_FILE_PATH = 'logging.config.yml'

with open(LOGGING_CONFIG_YAML_FILE_PATH) as config_fin:
    logging.config.dictConfig(yaml.safe_load(config_fin))

app = Flask(__name__)
app.bank = CompositeAssetItem(name='asset_composite')


@app.route(f'{API_ROUTE}/calculate_revenue')
def calc_assets_revenue():
    """
    Provides path to calculate total revenue for web_service
    :return: total revenue for all assets behind all periods provided (in json)
    """
    app.logger.info('called "%s/calculate_revenue" route', API_ROUTE)

    response = requests.get(CBR_KEY_INDICATORS_URL)
    if response.status_code >= 400:
        abort(503)
        app.logger.error(
            '%s service is unavailable now, get request status code: %s',
            CBR_KEY_INDICATORS_URL,
            response.status_code
        )

    app.logger.debug(
        'get request has sent to %s, status code: %s',
        CBR_KEY_INDICATORS_URL,
        response.status_code
    )

    key_indicators_col = parse_cbr_key_indicators_html(response.text)

    response = requests.get(CBR_CURRENCY_RATE_URL)
    if response.status_code >= 400:
        abort(503)
        app.logger.error(
            '%s service is unavailable now, get request status code: %s',
            CBR_CURRENCY_RATE_URL,
            response.status_code
        )

    app.logger.debug('get request has sent to %s, status code: %s', CBR_CURRENCY_RATE_URL, response.status_code)

    currency_rate_col = parse_cbr_currency_daily_html(response.text)
    period_list = list(map(lambda x: abs(int(x)), request.args.getlist('period')))
    result = app.bank.calculate_revenue(period_list, key_indicators_col, currency_rate_col)

    return jsonify(result)


@app.route(f'{API_ROUTE}/get')
def get_asset_list_with_provided_names():
    """
    Provides path to query web service to get assets with names provided
    :return: list of assets according to the provided names (in json)
    """
    app.logger.info('called "%s/get" route', API_ROUTE)
    name_list = request.args.getlist('name')
    result = app.bank.get_asset_list(name_list)

    return jsonify(result)


@app.route(f'{API_ROUTE}/cleanup')
def clean_asset_list():
    """Provides path to clean all assets stored"""
    app.logger.info('called "%s/cleanup" route', API_ROUTE)
    del app.bank
    app.bank = CompositeAssetItem(name='asset_composite')

    return 'assets list has been cleaned', 200


@app.route(f'{API_ROUTE}/list')
def get_asset_list():
    """
    Provides path to get list of all assets
    :return: list of all assets stored (in json)
    """
    app.logger.info('called "%s/list" route, run get_asset_list function', API_ROUTE)
    result = app.bank.get_asset_list()

    return jsonify(result)


@app.route(f'{API_ROUTE}/add/<char_code>/<name>/<capital>/<interest>')
def add_asset_item(char_code, name, capital, interest):
    """Provides path to add new assets for web service"""
    app.logger.info(
        'called "%s/add/%s/%s/%s/%s" route',
        API_ROUTE,
        char_code,
        name,
        capital,
        interest
    )

    capital = float(capital)
    interest = float(interest)
    if app.bank.get_asset_list(name_list=[name]):
        abort(403)
        app.logger.warning('asset with name %s has already existed', name)

    if interest <= 0 or interest >= 1 or capital <= 0:
        abort(400)
        app.logger.warning('bad values for %s or %s', interest, capital)

    app.bank.add(AssetItem(name, char_code, capital, interest))

    app.logger.info('asset %s was successfully added', name)

    return f'Asset {name} was successfully added.', 200


@app.route(JSON_DAILY_ROUTE)
def get_currency_rate_collection():
    """
    Provides path to get actual daily currency rate from cbr.ru
    :return: currency index (in json)
    """
    app.logger.info('called "%s" route', JSON_DAILY_ROUTE)
    response = requests.get(CBR_CURRENCY_RATE_URL)
    app.logger.debug(
        'get request has sent to %s, status code: %s',
        CBR_CURRENCY_RATE_URL,
        response.status_code
    )

    if response.status_code >= 400:
        app.logger.error(
            '%s service is unavailable now, get request status code: %s',
            CBR_CURRENCY_RATE_URL,
            response.status_code
        )
        abort(503)

    currency_index = parse_cbr_currency_daily_html(response.text)

    return jsonify(currency_index)


@app.route(JSON_KEY_INDICATORS_ROUTE)
def get_key_indicator_collection():
    """
    Provides path to get actual key indicator values from cbr.ru
    :return: currency index (in json)
    """
    app.logger.info('called "%s" route', JSON_KEY_INDICATORS_ROUTE)
    response = requests.get(CBR_KEY_INDICATORS_URL)
    app.logger.debug('get request has sent to %s, status code: %s', CBR_KEY_INDICATORS_URL, response.status_code)

    if response.status_code >= 400:
        app.logger.error(
            '%s service is unavailable now, get request status code: %s',
            CBR_KEY_INDICATORS_URL,
            response.status_code
        )
        abort(503)

    key_indicator_collection = parse_cbr_key_indicators_html(response.text)

    return jsonify(key_indicator_collection)


@app.errorhandler(404)
def page_not_found():
    return render_template('page_not_found.html'), 404


@app.errorhandler(503)
def page_not_found():
    return 'CBR service is unavailable', 503


def parse_cbr_currency_daily_html(html_document: str) -> dict:
    f"""
    Function to parse html of {CBR_CURRENCY_RATE_URL} page 
    :return: actual daily currency rate as dict ("currency": value)
    """
    currency_index = {}

    root = etree.fromstring(html_document, etree.HTMLParser())
    char_code_collection = root.xpath("//table[@class='data']//tr/td[2]/text()")
    unit_cnt = root.xpath("//table[@class='data']//tr/td[3]/text()")
    rate_collection = root.xpath("//table[@class='data']//tr/td[5]/text()")

    for code, rate, cnt in zip(char_code_collection, rate_collection, unit_cnt):
        currency_index[code] = round(float(rate) / float(cnt), 8)

    app.logger.debug('currency_index with %s items is built', len(currency_index))

    return currency_index


def parse_cbr_key_indicators_html(html_document: str) -> dict:
    f"""
    Function to parse html of {CBR_KEY_INDICATORS_URL} page 
    :return: actual key indicator values as dict ("indicator": value)
    """
    key_indicator_collection = {}

    root = etree.fromstring(html_document, etree.HTMLParser())
    char_code_collection = root.xpath(
        '//div[@class="dropdown"][1]//div[@class="col-md-3 offset-md-1 _subinfo"]/text()'
    )
    rate_collection = root.xpath(
        '//div[@class="dropdown"][1]//td[@class="value td-w-4 _bold _end mono-num"]/text()'
    )

    for code, rate in zip(char_code_collection, rate_collection):
        key_indicator_collection[code] = float(rate.replace(',', ''))

    app.logger.debug('currency_index with %s items is built', len(key_indicator_collection))

    return key_indicator_collection
