from argparse import Namespace
from collections import namedtuple
from unittest.mock import patch
import pytest

from asset_web_service import (
    app,
    AssetItem,
    CBR_CURRENCY_RATE_URL,
    CBR_KEY_INDICATORS_URL,
    CompositeAssetItem,
    JSON_DAILY_ROUTE,
    JSON_KEY_INDICATORS_ROUTE,
    parse_cbr_currency_daily_html,
    parse_cbr_key_indicators_html,
    requests,
)

CBR_CURRENCY_DAILY_HTML_SNAPSHOT = 'cbr_currency_base_daily.html'
CBR_KEY_INDICATORS_HTML_SNAPSHOT = 'cbr_key_indicators.html'
CURRENCY_DAILY_RATE_CNT = 34
KEY_INDICATORS_CNT = 6


@pytest.mark.skipif(1 == 0, reason='skip if no internet connection')
@pytest.mark.parametrize(
    ('requested_url', 'expected_status_code'),
    [
        pytest.param(JSON_DAILY_ROUTE, 200, id='requested url:' + CBR_CURRENCY_RATE_URL),
        pytest.param(JSON_KEY_INDICATORS_ROUTE, 200, id='requested url:' + CBR_KEY_INDICATORS_URL),
    ]
)
def test_service_make_request_to_cbr_cite_successfully(client, requested_url, expected_status_code):
    response = client.get(requested_url)
    assert expected_status_code == response.status_code


@pytest.mark.skipif(1 == 0, reason='skip if no internet connection')
@pytest.mark.parametrize(
    ('url', 'snapshot_file_path', 'parse_function'),
    [
        pytest.param(
            CBR_CURRENCY_RATE_URL,
            CBR_CURRENCY_DAILY_HTML_SNAPSHOT,
            parse_cbr_currency_daily_html,
            id=CBR_CURRENCY_RATE_URL),
        pytest.param(
            CBR_KEY_INDICATORS_URL,
            CBR_KEY_INDICATORS_HTML_SNAPSHOT,
            parse_cbr_key_indicators_html,
            marks=[pytest.mark.skipif(1 == 1, reason="page could temporary changes its html")],
            id=CBR_KEY_INDICATORS_URL),
    ]
)
def test_cbr_snapshot_format_still_actual(url, snapshot_file_path, parse_function):
    with open(snapshot_file_path, 'r') as f_in:
        snapshot_html = f_in.read()

    snapshot_parsed = parse_function(snapshot_html)
    current_web_page_parsed = parse_function(requests.get(url).text)

    assert len(snapshot_parsed) == len(current_web_page_parsed)


def test_can_parse_cbr_currency_daily_html_correctly():
    with open(CBR_CURRENCY_DAILY_HTML_SNAPSHOT, 'r') as f_in:
        html_document = f_in.read()
    currency_index = parse_cbr_currency_daily_html(html_document)
    assert CURRENCY_DAILY_RATE_CNT == len(currency_index), (
        f"expected len of index is {CURRENCY_DAILY_RATE_CNT}, but got index with len {len(currency_index)}"
    )
    assert all(len(key) == 3 for key in currency_index.keys()), "char code should consist 3 letters"
    assert 57.0229 == currency_index['AUD'], (
        f"rate for AUD char code should be 57.0229, but got rate: {currency_index['AUD']}"
    )
    assert round(14.4485 / 100, 8) == currency_index['AMD'], (
        f"rate for AMD char code should be {round(14.4485 / 100, 8)}, but got rate: {currency_index['AMD']}"
        f"check that returns value per unit"
    )


def test_can_parse_cbr_key_indicators():
    with open(CBR_KEY_INDICATORS_HTML_SNAPSHOT, 'r') as f_in:
        html_document = f_in.read()
    key_indicators_index = parse_cbr_key_indicators_html(html_document)
    assert KEY_INDICATORS_CNT == len(key_indicators_index), (
        f"expected len of index is {KEY_INDICATORS_CNT}, but got index with len {len(key_indicators_index)}"
    )
    assert 4366.17 == key_indicators_index['Au'], (
        f"rate for Au char code should be 4366.17, but got rate: {key_indicators_index['Au']}"
    )


@pytest.fixture(scope='module')
def client():
    with app.test_client() as client:
        yield client


def test_service_reply_to_incorrect_path(client, capsys):
    response = client.get('/not_existing_route')
    assert 404 == response.status_code
    assert 'This route is not found' in response.data.decode(response.charset)

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


@pytest.mark.parametrize(
    'route',
    [
        pytest.param(JSON_DAILY_ROUTE, id=JSON_DAILY_ROUTE),
        pytest.param(JSON_KEY_INDICATORS_ROUTE, id=JSON_KEY_INDICATORS_ROUTE),
        pytest.param('/api/asset/calculate_revenue?period=1', id='/api/asset/calculate_revenue')
    ]
)
def test_service_get_503_status_code_when_cbr_site_unavailable(client, capsys, route):
    with patch.object(
            requests,
            'get',
            return_value=Namespace(status_code=503)
    ):
        response = client.get(route)

    assert 503 == response.status_code
    assert 'CBR service is unavailable' in response.data.decode(response.charset)

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


def test_service_make_get_currency_rate_in_json(client, capsys):
    with open(CBR_CURRENCY_DAILY_HTML_SNAPSHOT, 'r') as f_in:
        html_document = f_in.read()

    with patch.object(
            requests,
            'get',
            return_value=Namespace(status_code=200, text=html_document)
    ):
        response = client.get(JSON_DAILY_ROUTE)
    assert 200 == response.status_code
    assert response.is_json

    currency_index = response.json
    assert CURRENCY_DAILY_RATE_CNT == len(currency_index.keys())
    assert all(len(key) == 3 for key in currency_index.keys()), "char code should consist 3 letters"
    assert 57.0229 == currency_index['AUD'], (
        f"rate for AUD char code should be 57.0229, but got rate: {currency_index['AUD']}"
    )

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


def test_service_make_get_key_indicators_in_json(client, capsys):
    with open(CBR_KEY_INDICATORS_HTML_SNAPSHOT, 'r') as f_in:
        html_document = f_in.read()

    with patch.object(
            requests,
            'get',
            return_value=Namespace(status_code=200, text=html_document)
    ):
        response = client.get(JSON_KEY_INDICATORS_ROUTE)
    assert 200 == response.status_code
    assert response.is_json

    key_indicators_collection = response.json
    assert KEY_INDICATORS_CNT == len(key_indicators_collection.keys())
    assert 73.7961 == key_indicators_collection['USD'], (
        f"rate for AUD char code should be 73.7961, but got rate: {key_indicators_collection['USD']}"
    )

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


@pytest.fixture()
def asset_test_collection():
    Asset_nt = namedtuple('asset', ['item', 'list_repr'])

    asset_1 = AssetItem(name='asset_EUR', char_code='EUR', capital=2_000, interest=0.05)
    asset_li_repr_1 = [['EUR', 'asset_EUR', 2_000, 0.05]]

    asset_2 = AssetItem(name='asset_RUB', char_code='RUB', capital=100_000, interest=0.15)
    asset_li_repr_2 = [['RUB', 'asset_RUB', 100_000, 0.15]]

    asset_3 = AssetItem(name='asset_USD', char_code='USD', capital=1_000, interest=0.1)
    asset_li_repr_3 = [['USD', 'asset_USD', 1_000, 0.1]]

    asset_4 = AssetItem(name='asset_XDR', char_code='XDR', capital=1_500, interest=0.12)
    asset_li_repr_4 = [['XDR', 'asset_XDR', 1_500, 0.12]]

    asset_collection = (
        Asset_nt(asset_1, asset_li_repr_1),
        Asset_nt(asset_2, asset_li_repr_2),
        Asset_nt(asset_3, asset_li_repr_3),
        Asset_nt(asset_4, asset_li_repr_4),
    )

    return asset_collection


def test_composite_store_assets_correctly(asset_test_collection):
    asset_1 = asset_test_collection[2].item
    asset_2 = asset_test_collection[1].item
    composite_asset_store = CompositeAssetItem(
        name='asset_store',
        asset_collection=[asset_1, asset_2]
    )
    etalon_result = asset_test_collection[1].list_repr + asset_test_collection[2].list_repr
    assert etalon_result == composite_asset_store.get_asset_list()

    asset_3 = asset_test_collection[0].item
    composite_asset_store.add(asset_3)
    etalon_result = asset_test_collection[0].list_repr + etalon_result
    assert etalon_result == composite_asset_store.get_asset_list()

    name_list = ['asset_EUR', 'asset_USD']
    etalon_result.pop(1)
    assert etalon_result == composite_asset_store.get_asset_list(name_list)


@pytest.mark.parametrize(
    ('asset_index_list', 'period_list', 'true_revenue_dict'),
    [
        pytest.param([0], [1, 2], {'1': 8933.04, '2': 18312.732}, id='asset_EUR; periods 1, 2'),
        pytest.param([0, 1, 2], [2], {'2': 66097.167}, id='asset_EUR_RUB_USD; period 2'),
        pytest.param([0, 2], [1, 3], {'1': 16330.390000000001, '3': 52646.6371}, id='asset_EUR_USD; period 1 3'),
        pytest.param(
            [0, 3],
            [1, 2, 5],
            {'1': 19148.49, '2': 39969.486000000004, '5': 114257.87954521},
            id='asset_EUR_AUD (need to use currency rate); period 1 2 5'
        )
    ]
)
def test_composite_calc_assets_revenue_correctly(
        asset_test_collection,
        asset_index_list,
        period_list,
        true_revenue_dict
):
    key_indicator_collection = {'USD': 73.9735, 'EUR': 89.3304, 'Au': 4361.69}
    currency_rate_collection = {'XDR': 56.7525}
    composite_asset_store = CompositeAssetItem(
        name='asset_store',
        asset_collection=[asset_test_collection[i].item for i in asset_index_list]
    )
    result = composite_asset_store.calculate_revenue(
        period_list,
        key_indicator_collection,
        currency_rate_collection
    )
    assert true_revenue_dict == result


@pytest.mark.parametrize(
    ('route', 'expected_status_code', 'message'),
    [
        pytest.param('USD/asset_USD/1000/0.1', 200, 'Asset asset_USD was successfully added'),
        pytest.param('RUB/asset_RUB/100000/0.15', 200, 'Asset asset_RUB was successfully added'),
        pytest.param('EUR/asset_EUR/2000/0.05', 200, 'Asset asset_EUR was successfully added'),
        pytest.param('XDR/asset_XDR/1500/0.12', 200, 'Asset asset_XDR was successfully added'),
        pytest.param('XDR/asset_XDR/15000/0.15', 403, '', id='asset already exist'),
        pytest.param('AUS/asset_AUS/15000/2', 400, '', id='bad value for interest'),
        pytest.param('AUF/asset_AUF/-15000/0.15', 400, '', id='bad value for capital')
    ]
)
def test_service_can_add_assets_in_store(client, route, expected_status_code, message, capsys):
    full_route = f'/api/asset/add/{route}'
    response = client.get(full_route)
    assert expected_status_code == response.status_code
    assert message in response.data.decode(response.charset)

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


def test_service_can_return_assets_list(client, asset_test_collection, capsys):
    response = client.get('/api/asset/list')
    etalon_result = []
    for asset in asset_test_collection:
        etalon_result += asset.list_repr
    assert 200 == response.status_code
    assert response.is_json

    result = response.json
    assert etalon_result == result

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


@pytest.mark.parametrize(
    ('route', 'asset_index_list'),
    [
        pytest.param('name=asset_USD&name=asset_RUB', [1, 2], id='USD and RUB'),
        pytest.param('name=asset_GGG', [], id='wrong name'),
        pytest.param(
            'name=asset_USD&name=asset_EUR&name=asset_XDR&name=asset_RUB',
            [0, 1, 2, 3],
            id='all names'
        )
    ]
)
def test_service_can_return_assets_list_with_provided_names(
        client,
        asset_test_collection,
        route,
        asset_index_list,
        capsys
):
    response = client.get(f'/api/asset/get?{route}')
    etalon_result = []
    for i in asset_index_list:
        etalon_result += asset_test_collection[i].list_repr

    assert 200 == response.status_code
    assert response.is_json

    result = response.json
    assert etalon_result == result

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


def read_file(url: str) -> Namespace:
    if url == CBR_KEY_INDICATORS_URL:
        file_path = CBR_KEY_INDICATORS_HTML_SNAPSHOT
    elif url == CBR_CURRENCY_RATE_URL:
        file_path = CBR_CURRENCY_DAILY_HTML_SNAPSHOT
    else:
        raise AssertionError

    with open(file_path, 'r') as f_in:
        result = f_in.read()

    return Namespace(text=result, url=url, status_code=200)


@pytest.mark.parametrize(
    ('route', 'true_result'),
    [
        pytest.param('period=1', {'1': 50930.142}, id='period 1 year'),
        pytest.param(
            'period=2&period=5&period=10',
            {'2': 107646.77634, '5': 320150.36198168, '10': 878631.11308631},
            id='periods 2, 5, 10 years'
        )
    ]
)
def test_service_can_calculate_assets_revenue_behind_periods_provided(client, route, true_result, capsys):
    with patch.object(requests, 'get', side_effect=read_file):
        response = client.get(f'/api/asset/calculate_revenue?{route}')

    assert 200 == response.status_code
    assert response.is_json

    result = response.json
    assert true_result == result

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'


def test_service_can_clean_assets_store(client, capsys):
    response = client.get('/api/asset/cleanup')
    assert 200 == response.status_code

    response = client.get('/api/asset/list')
    result = response.json
    assert [] == result

    captured = capsys.readouterr()
    assert '' == captured.out, 'stdout must be empty'
