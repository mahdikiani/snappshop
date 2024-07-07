import asyncio
import datetime
import json
import logging
import mimetypes
import os
from functools import lru_cache
from pathlib import Path

import aiohttp
import gspread
import pandas as pd
import requests
from aiocache import cached
from google.oauth2 import service_account
from gspread_dataframe import get_as_dataframe

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxMDUiLCJqdGkiOiJiMDMzMjc2OTcxNDc5ODJlMTk2OGYxZmUwNjA4YTg3NGIyZTQyM2ZlYmFhZmFhYWIwZmZkYjNhOWQwNDkxY2Q4ZDQ2NGQ1N2JhZTEzZjc0NiIsImlhdCI6MTcxODg2OTgyNy44MDAyMDgsIm5iZiI6MTcxODg2OTgyNy44MDAyMTEsImV4cCI6MTcxOTQ3NDYyNy43OTQ1NzcsInN1YiI6IjIzNDU0OTkiLCJzY29wZXMiOlsicm9sZTpzZWxsZXIiXSwiYXV0aG9yaXphdGlvbl9kZXRhaWxzIjpbeyJ0eXBlIjoicHVzaCIsImxvY2F0aW9ucyI6WyJjbHVzdGVyOjEwNS92aG9zdDpwcy9xdWV1ZTptcXR0LSovcm91dGluZy1rZXk6di1xSnBPbmciLCJjbHVzdGVyOjEwNS92aG9zdDpwcy9xdWV1ZTptcXR0LSovcm91dGluZy1rZXk6di1EalZtOVciLCJjbHVzdGVyOjEwNS92aG9zdDpwcy9xdWV1ZTptcXR0LSovcm91dGluZy1rZXk6di1ndzRPbTIiXSwiYWN0aW9ucyI6WyJyZWFkIiwid3JpdGUiLCJjb25maWd1cmUiXX0seyJ0eXBlIjoicHVzaCIsImxvY2F0aW9ucyI6WyJjbHVzdGVyOjEwNS92aG9zdDpwcy9leGNoYW5nZTphbXEudG9waWMvcm91dGluZy1rZXk6di1xSnBPbmciLCJjbHVzdGVyOjEwNS92aG9zdDpwcy9leGNoYW5nZTphbXEudG9waWMvcm91dGluZy1rZXk6di1EalZtOVciLCJjbHVzdGVyOjEwNS92aG9zdDpwcy9leGNoYW5nZTphbXEudG9waWMvcm91dGluZy1rZXk6di1ndzRPbTIiXSwiYWN0aW9ucyI6WyJyZWFkIl19XX0.jMFvJR3be9e4GTzh1c6MWOEzoqzzRJMHhur6ecuW6OuNtb1LrlVEdi32x4QeaCb21GqfqXL3dqwb8xKCVeOAyITehXpuz6FeGGeSS-ErQ21WPuTaI7zqYyed0bRSN58n85x7ZmCNr6xlxo2IF_zG_v3CIkEQGbhrX0HjB8e_tp1mAwpEv8jVLRWufzZS8TdrXsNk996MEabp4dkvJyy5_rnYAqe-2rCBvLP6C_TuXlOxGwO7QsUmyPq9xs0FHXKoJXrqBaVyXWmfyEXOEsQv_CUdVtlzyQRgg925jJnMlZgYwPrFXyQ2if-bu1pIVsVKwNE9TigRYuP-24hcJolFUV45ihEgeXCnpJR3kCH003hbUWqc8_odu2Ev19FTRiboxmU2DMrRT0WRM3bznOuZBc0g4t4MSMy7qexU6I7-A9a1W8ljOIKh86SpAKxzO95bHzVm_s6dKHhypXqQG0etz9-ZNZADygnky6vm6ktuaGJUr45XLFN9Jq3HBZW7NrKCBUG75yjtjffFR1vQSNP7K7yW1IQOoLxzMUZUIFKYQXyE053f6bkw40Er3YcnIMpcUMEgyiQwIYGsjCFnTbglNGjW_R7IlR7HcXQ7z8f9rhJFsV5yCF1T8tfn96YvvG0gFGxxfrKl5yN-jDkd19VCKC5rTiKWzKwEPasV-txI4dE"

try:
    base_dir = Path(os.path.dirname(__file__))
except NameError:
    base_dir = Path(".")
images_dir = base_dir / "images"
product_list = [
    {
        "code": "SG10002",
        "images": [images_dir / "SG10002" / "SG10002_18.jpg", images_dir / "z918.jpg"],
    },
    {
        "code": "SG10003",
        "images": [images_dir / "SG10003" / "SG10003_18.jpg", images_dir / "z918.jpg"],
    },
]
description = """موضوعی که در شمش طلا بسیار ارزش دارد و از اهمیت بالایی برخوردار است، عیار و وزن آن میباشد. هرچه عیار سکه بالا باشد، قیمت آن بیشتر می‌شود. امروزه به دلیل تنوع زیاد در محصولات کادویی، انتخاب یک هدیه مناسب از لحاظ قیمت کمی سخت‌تر شده است. با این حال یک شمش با عیار و ورن متناسب با بودجه شما می‌تواند انتخاب مناسب و با ارزشی باشد. به علاوه یکی از جذاب‌ترین و جالب‌ترین بخش‌های بازار طلا خرید و فروش شمش است. خیلی از افراد در این بازار سرمایه‌گذاری می‌کنند. از مشکلاتی که به هنگام خرید سکه پیش می‌آید افزایش قیمت آن است ازاین‌جهت خرید شمش گرمی رواج پیدا کرد. شمش گرمی از جدیدترین نوع طلاست که در سال‌های اخیر به بازار عرضه شده است. شمش های مدوپد در وزن های مختلف این امکان را به شما می دهد که با هر بودجه ای بتوانید طلا با کمترین قیمت را خریداری نمائید."""

snapp_ingot_category_id = "aD5Zbg"
snapp_modopod_brand_id = "DYk3K0"
product_title_template = "شمش طلا 18 عیار مدوپد مدل {product_code}"
product_weight_list = [i / 10 for i in range(1, 10)] + list(range(1, 11))
product_size_list = []


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Proxy(metaclass=Singleton):
    schema = "socks5"
    user = "socks_user"
    password = "0c1a2375a0fe6d6934f3266779d4e316dc8933f81143ad"
    host = "a4a33997-6881-45de-8b63-014aa75d9afe.hsvc.ir"
    port = 30164

    def __init__(self):
        self.addr = (
            f"{self.schema}://{self.user}:{self.password}@{self.host}:{self.port}"
        )
        # self.addr = "https://socks.liara.run"

    @property
    def proxy(self):
        return {"http": self.addr, "https": self.addr}


class SnappShop(metaclass=Singleton):
    def __init__(self):
        self.base_url = "https://apix.snappshop.ir"
        self.endpoints = {
            "vendors": "vendors/v1",
            "catalog": "catalog/v1",
            "products": "products/v1",
            "categories": "categories/v1",
            "brands": "brands/v1",
        }
        self.headers = {
            "accept": "application/json",
            "accept-language": "en,en-US;q=0.9,fa-IR;q=0.8,fa;q=0.7",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "content-type": "application/json",
            "origin": "https://seller.snappshop.ir",
            "priority": "u=1, i",
            "referer": "https://seller.snappshop.ir/",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "uuid": "9a7d81ae-2b36-4f5c-b2dc-18911bc84d64",
            "x-client-type": "seller",
        }

    async def _aio_request_session(
        self,
        session: aiohttp.ClientSession,
        *,
        method: str = "get",
        url: str = None,
        **kwargs,
    ) -> dict:
        if url is None:
            raise ValueError("url is required")
        if not url.startswith("http"):
            url = f"https://{url}"

        raise_exception = kwargs.pop("raise_exception", True)

        async with session.request(method, url, **kwargs) as response:
            if raise_exception:
                response.raise_for_status()
            return await response.json()

    async def _aio_request(self, method="get", url: str = None, **kwargs) -> dict:
        if url is None:
            endpoint = kwargs.pop("endpoint", "vendors")
            path = kwargs.pop("path", "")
            url = f"{self.base_url}/{self.endpoints.get(endpoint)}/{path}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            return await self._aio_request_session(
                session, method=method, url=url, **kwargs
            )

    def _request(self, method="get", endpoint=None, data={}, **kwargs):
        base_url = kwargs.pop("base_url", self.vendor_url)
        url = f"{base_url}/{endpoint}"
        raise_exception = kwargs.pop("raise_exception", True)
        res = requests.request(method, url, headers=self.headers, json=data, **kwargs)
        if raise_exception:
            res.raise_for_status()
        return res

    @cached()
    async def get_category(self, category_name, depth=1, id=None):
        params = {"depth": depth}
        if id:
            params["id"] = id
        categories: list[dict] = (
            await self._aio_request(endpoint="categories", params=params)
        ).get("data")
        for category in categories:
            if category.get("title") == category_name:
                return category
        return None

    @cached()
    async def get_brand(self, brand_name):
        brands: list[dict] = (
            await self._aio_request(endpoint="brands", params={"query": brand_name})
        ).get("data")
        for brand in brands:
            if brand.get("title") == brand_name:
                return brand
        return None

    @cached()
    async def seller_info(self, **kwargs):
        return await self._aio_request(endpoint="vendors", path="seller-info", **kwargs)

    @cached()
    async def options(self, page=1, weightOrSize="weight", **kwargs):
        if weightOrSize == "weight":
            cid = kwargs.get("weight", "60rdDw")
        else:
            cid = kwargs.get("size", "lgwWgo")
        return self._request(
            endpoint=f"attributes/{cid}/options?page={page}",
            base_url=self.catalog_url,
            **kwargs,
        )

    def selected_variations(self, **kwargs):
        if kwargs.get("weightOrSize", "weight") == "weight":
            if not product_weight_list:
                return []
        elif kwargs.get("weightOrSize", "weight") == "size":
            if not product_size_list:
                return []

        if (base_dir / f'{kwargs.get("weightOrSize", "weight")}.json').exists():
            with open(
                base_dir / f'{kwargs.get("weightOrSize", "weight")}.json',
                encoding="utf-8",
            ) as f:
                options = json.load(f)
        else:
            options = {}

        if datetime.datetime.strptime(
            options.get("created", "2000-01-01 00:00:01"), "%Y-%m-%d %H:%M:%S"
        ) > datetime.datetime.now() - datetime.timedelta(days=30):
            options_data = options.get("data")
        else:
            options_data = []
            for p in range(1, 51):
                options = self.options(page=p, **kwargs).json()
                if not options.get("data"):
                    break
                options_data.extend(options.get("data"))

            with open(
                base_dir / f'{kwargs.get("weightOrSize", "weight")}.json',
                "w",
                encoding="utf-8",
            ) as f:
                options["created"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                options["data"] = options_data
                json.dump(options, f, indent=4, ensure_ascii=False)

        found_options = []
        for op in options_data:
            for weight in product_weight_list:
                if (
                    op.get("admin_name") == f"{weight}"
                    or op.get("admin_name") == f"{weight} گرم"
                ):
                    # print(weight, op.get("admin_name"))
                    found_options.append(op)
        return [{"id": fo.get("id")} for fo in found_options]

    def create_product_quote(self, product_code, **kwargs):
        json_data = {
            "step": "general",
            "category_id": snapp_ingot_category_id,
            "brand_id": snapp_modopod_brand_id,
            "is_original": True,
            "title": product_title_template.format(product_code=product_code),
            "title_en": "",
            "description": description,
            "related_links": "",
            "type": "product",
        }
        return self._request(
            method="post", endpoint="DjVm9W/product-quotes", data=json_data, **kwargs
        )

    def add_weights_options(self, pid, **kwargs):
        json_data = {
            "step": "variations",
            "variations": [
                {
                    "id": "lgwWgo",
                    "options": self.selected_variations(weightOrSize="size"),
                },
                {
                    "id": "60rdDw",
                    "options": self.selected_variations(weightOrSize="weight"),
                },
            ],
            "type": "product",
        }

        return self._request(
            method="patch",
            endpoint=f"DjVm9W/product-quotes/{pid}",
            data=json_data,
            **kwargs,
        )

    def add_material(self, pid, **kwargs):
        json_data = {
            "step": "attributes",
            "attributes": [
                {
                    "id": "0QYoo0",
                    "option": {
                        "id": "qJX1wg",
                        "admin_name": "شمش",
                        "name": "شمش",
                        "label": None,
                        "swatch_value": None,
                    },
                    "type": "select",
                },
                {
                    "id": "gwbl4D",
                    "option": {
                        "id": "D5ZPrg",
                        "admin_name": "18",
                        "name": "18",
                        "label": None,
                        "swatch_value": None,
                    },
                    "type": "select",
                },
                {
                    "id": "dq6930",
                    "option": {
                        "id": "geGzJR",
                        "admin_name": "طلا",
                        "name": "طلا",
                        "label": None,
                        "swatch_value": None,
                    },
                    "type": "select",
                },
            ],
            "type": "product",
        }

        return self._request(
            method="patch",
            endpoint=f"DjVm9W/product-quotes/{pid}",
            data=json_data,
            **kwargs,
        )

    def add_images(self, pid, images_path, **kwargs):
        responses = []
        for i, image_path in enumerate(images_path):
            mime_type, _ = mimetypes.guess_type(image_path)

            files = {
                "image": (image_path.name, open(image_path, "rb"), mime_type),
            }

            data = {"is_main": "true" if i == 0 else "false"}

            headers = {
                "accept": "application/json",
                "accept-language": "en,en-US;q=0.9,fa-IR;q=0.8,fa;q=0.7",
                "authorization": f"Bearer {ACCESS_TOKEN}",
                "origin": "https://seller.snappshop.ir",
                "referer": "https://seller.snappshop.ir/",
                "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                # "content-type": "multipart/form-data",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "uuid": "9a7d81ae-2b36-4f5c-b2dc-18911bc84d64",
                "x-client-type": "seller",
            }
            url = f"{self.vendor_url}/DjVm9W/product-quotes/{pid}/images"
            r = requests.post(url, headers=headers, files=files, data=data, **kwargs)

            responses.append(r)
        return responses

    def submit(self, pid, **kwargs):
        return self._request(
            "patch",
            f"DjVm9W/product-quotes/{pid}/submit",
            **kwargs,
        )

    def add_to_shop(self, pid, **kwargs):
        variants = self.shop_variants()
        for variant in variants:
            with open(base_dir / "products_done.json", encoding="utf-8") as f:
                done = json.load(f)
            if pid in done and variant["id"] in done[pid]:
                continue

            json_data = {
                "warranty_id": "x0QZq8",
                "lead_time": 1,  # how mant days
                "product_id": pid,  # "xdp2RP",
                "packaging_height": 1,
                "packaging_length": 10,
                "packaging_width": 10,
                "packaging_weight": 50,
                "has_express_delivery": True,
                "variations": [
                    {
                        "attribute_id": "60rdDw",
                        "attribute_value": variant["id"],
                    },
                ],
                "stock": 100,
                "price": variant["price"] // 10,
                "capacity": 3,
            }

            self._request(
                method="post",
                endpoint="DjVm9W/inventory/products",
                data=json_data,
                **kwargs,
            )

            done[pid] = done.get(pid, [])
            done[pid].append(variant["id"])
            with open(base_dir / "products_done.json", "w", encoding="utf-8") as f:
                json.dump(done, f, ensure_ascii=False, indent=4)
            logging.warning(f'Added product {pid} with variant {variant["id"]} to shop')

    def product_list(self, **kwargs):
        if (base_dir / "products.json").exists():
            with open(
                base_dir / "products.json",
                encoding="utf-8",
            ) as f:
                products = json.load(f)
            if datetime.datetime.strptime(
                products.get("created", "2000-01-01 00:00:01"), "%Y-%m-%d %H:%M:%S"
            ) > datetime.datetime.now() - datetime.timedelta(days=30):
                return products

        products_data = []
        for page in range(1, 100):
            res = self._request(
                endpoint="inventory-management/products",
                params={
                    "category_id": "rg3LA0",
                    "brand_id": snapp_modopod_brand_id,
                    "page": page,
                },
                base_url=self.product_url,
                **kwargs,
            )
            products_data.extend(res.json().get("data"))
        result = res.json()
        result["data"] = products_data

        with open(
            base_dir / "products.json",
            "w",
            encoding="utf-8",
        ) as f:
            result["created"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            json.dump(result, f, indent=4, ensure_ascii=False)

        return result

    def shop_variants(
        self,
    ):
        prices_variants = {
            0.1: 4656900,
            0.2: 8448900,
            # 0.25: 10561100,
            0.3: 12316400,
            0.4: 16421800,
            0.5: 20329000,
            0.6: 24394800,
            0.7: 28460600,
            0.8: 32209100,
            0.9: 36235200,
            1: 40261300,
            # 1.2: 46885700,
            # 1.5: 58607100,
            2: 78142800,
            3: 117388200,
            4: 156285700,
            # 4.5: 175821400,
            5: 195357200,
            6: 234428600,
            7: 273500100,
            8: 312571500,
            9: 351642900,
            10: 390714400,
        }

        self.selected_variations()

        with open(base_dir / "weight.json", encoding="utf-8") as f:
            options = json.load(f)
        options_data = options.get("data")
        found_options = []
        for op in options_data:
            for weight, price in prices_variants.items():
                if (
                    # op.get("admin_name") == f"{weight}"
                    # or
                    op.get("admin_name")
                    == f"{weight} گرم"
                ):
                    # print(weight, op.get("admin_name"))
                    found_options.append(dict(**op, price=price))

        return found_options


class Item:
    def __init__(self, data):
        self.__dict__.update(data)
        self.data = data

    async def get_category(self):
        snappshop = SnappShop()
        cid = None
        for i in range(1, 6):
            key = f"category_{i}"
            category = await snappshop.get_category(self.data.get(key), id=cid, depth=2)
            cid = category.get("id")
            if not category.get("has_children"):
                self.category_id = cid
                return cid
        self.category_id = cid
        return cid

    async def get_brand(self):
        snappshop = SnappShop()
        brand = await snappshop.get_brand(self.brand_name)
        self.brand_id = brand.get("id")
        return brand.get("id")

    def get_sizes(self):
        clean_str = self.weights.strip("[]")
        str_list = clean_str.split(",")
        float_list = [float(num.strip()) for num in str_list if num.strip()]
        return float_list

    async def get_sizes_id(self):
        pass


@lru_cache
def get_df() -> pd.DataFrame:
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://spreadsheets.google.com/feeds",
    ]
    credentials = service_account.Credentials.from_service_account_file(
        base_dir / "snappshop-access.json", scopes=scopes
    )

    gc = gspread.authorize(credentials)

    spreadsheet_id = "1sWOYcFiMFY0cxNBvK6Uc96exT7ZXhR5dpV6DnB1kcaQ"
    worksheet_name = "Sheet1"

    wb = gc.open_by_key(spreadsheet_id)
    sheet = wb.worksheet(worksheet_name)
    df = get_as_dataframe(sheet)
    return df


def get_item(index=0) -> Item:
    df = get_df()
    item = Item(df.loc[index].to_dict())
    return item


# %%


async def main():
    snappshop = SnappShop()
    item = get_item(0)
    await item.get_category()
    await item.get_brand()
    print(item.brand_id)
    print(await snappshop.seller_info())


if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__2":
    snappshop = SnappShop()
    products = snappshop.product_list()

    if not (base_dir / "products_done.json").exists():
        with open(base_dir / "products_done.json", "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    with open(base_dir / "products_done.json", encoding="utf-8") as f:
        done = json.load(f)

    for product in products.get("data"):
        try:
            pid = product.get("id")
            snappshop.add_to_shop(pid)

            # with open(base_dir / "products_done.json", "w", encoding="utf-8") as f:
            #     json.dump(done, f, ensure_ascii=False, indent=4)
        except Exception as e:
            if (base_dir / "products_error.json").exists():
                with open(base_dir / "products_error.json", encoding="utf-8") as f:
                    error = json.load(f)
            else:
                error = {}
            error[product.get("id")] = str(e)
            with open(base_dir / "products_error.json", "w", encoding="utf-8") as f:
                json.dump(error, f, indent=4, ensure_ascii=False)


def create_products():
    snappshop = SnappShop()
    snappshop.seller_info().json()

    if (base_dir / "done.json").exists():
        with open(base_dir / "done.json", encoding="utf-8") as f:
            done = json.load(f)
    else:
        done = {}

    for product_item in product_list:
        if product_item.get("code") in done:
            continue

        try:
            product: dict = snappshop.create_product_quote(
                product_item.get("code")
            ).json()
            pid = product.get("data", {}).get("id")
            # pid = "gNv54e"  # product.get("data", {}).get("id")
            snappshop.add_weights_options(pid)
            snappshop.add_material(pid)
            snappshop.add_images(pid, product_item.get("images"))
            p5 = snappshop.submit(pid)

            done[product_item.get("code")] = p5.json()

            with open(base_dir / "done.json", "w", encoding="utf-8") as f:
                json.dump(done, f, ensure_ascii=False, indent=4)
        except Exception as e:
            if (base_dir / "error.json").exists():
                with open(base_dir / "error.json", encoding="utf-8") as f:
                    error = json.load(f)
            else:
                error = {}
            error[product_item.get("code")] = str(e)
            with open(base_dir / "error.json", "w", encoding="utf-8") as f:
                json.dump(error, f, indent=4, ensure_ascii=False)
