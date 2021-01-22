"""Module to efficient store assets using composite design pattern"""
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional


class Component(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_asset_list(self):
        raise NotImplementedError

    @abstractmethod
    def calculate_revenue(self, period_li, key_indicator_col, currency_rate_col):
        raise NotImplementedError


class AssetItem(Component):
    def __init__(self, name: str, char_code: str, capital: float, interest: float):
        super().__init__(name)
        self.char_code = char_code
        self.capital = capital
        self.interest = interest

    def get_asset_list(self) -> list:
        asset = [self.char_code, self.name, self.capital, self.interest]
        return asset

    def calculate_revenue(self, period_li: list, key_indicator_col: dict, currency_rate_col: dict) -> dict:
        res = {}
        if self.char_code == 'RUB':
            rate = 1
        elif self.char_code in key_indicator_col.keys():
            rate = key_indicator_col[self.char_code]
        else:
            rate = currency_rate_col[self.char_code]

        for period in period_li:
            revenue = round(self.capital * rate * ((1.0 + self.interest) ** period - 1.0), 8)
            res[period] = revenue
        return res


class CompositeAssetItem(Component):
    def __init__(self, name: str, asset_collection: Optional[list] = None):
        super().__init__(name)
        self.asset_collection = []
        self.asset_collection.extend(asset_collection or [])

    def add(self, asset_item: AssetItem) -> None:
        self.asset_collection.append(asset_item)

    def get_asset_list(self, name_list: Optional[list] = None) -> list:
        name_list = name_list or []
        asset_li = [
            asset.get_asset_list() for asset in self.asset_collection
            if not name_list or asset.name in name_list
        ]
        return sorted(asset_li, key=lambda x: x[0])

    def calculate_revenue(self, period_li: list, key_indicator_col: dict, currency_rate_col: dict) -> dict:
        res = defaultdict(int)
        asset_revenue_dict_col = [
            asset.calculate_revenue(period_li, key_indicator_col, currency_rate_col) for asset in self.asset_collection
        ]

        for key in period_li:
            res[str(key)] = sum(map(lambda x: x[key], asset_revenue_dict_col))

        return dict(res)
