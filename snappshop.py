import asyncio
import json
import logging
import mimetypes
import os
from functools import lru_cache
from pathlib import Path

import aiohttp
import pandas as pd
from singleton import Singleton

import cache
import excel
from jwtoken import JWT

try:
    base_dir = Path(os.path.dirname(__file__))
except NameError:
    base_dir = Path(".")


@cache.file_cache()
async def get_category(categories):
    snappshop = SnappShop()
    cid = None
    for i, category in enumerate(categories):
        category = await snappshop.get_category(category, id=cid, depth=2)
        cid = category.get("id")
        if not category.get("has_children"):
            return cid
    return cid


class Item:
    def __init__(self, data):
        self.__dict__.update(data)
        self.size_ids = []
        self.weight_ids = []

    async def get_category(self):
        categories = [
            self.category_1,
            self.category_2,
            self.category_3,
            self.category_4,
            self.category_5,
        ]
        self.category_id = await get_category(categories)
        return self.category_id

    async def get_brand(self):
        snappshop = SnappShop()
        brand = await snappshop.get_brand(self.brand_name)
        self.brand_id = brand.get("id")
        return brand.get("id")

    def get_sizes(self):
        clean_str = self.sizes.strip("[]")
        str_list = clean_str.split(",")
        float_list = [float(num.strip()) for num in str_list if num.strip()]
        return float_list

    async def get_size_ids(self):
        snappshop = SnappShop()
        sizes = await snappshop.get_variants(self.get_sizes(), "size")
        self.size_ids = [{"id": size.get("id")} for size in sizes]
        return sizes

    def get_colors(self):
        clean_str = self.colors.strip("[]")
        str_list = clean_str.split(",")
        float_list = [s.strip() for s in str_list if s.strip()]
        return float_list

    async def get_color_ids(self):
        snappshop = SnappShop()
        colors = await snappshop.get_variants(self.get_colors(), "color")
        self.color_ids = [{"id": color.get("id")} for color in colors]
        return colors

    def get_weights(self):
        clean_str = self.weights.strip("[]")
        str_list = clean_str.split(",")
        float_list = [float(num.strip()) for num in str_list if num.strip()]
        return float_list

    async def get_weight_ids(self):
        snappshop = SnappShop()
        weights = await snappshop.get_variants(self.get_weights(), "weight")
        self.weight_ids = [{"id": size.get("id")} for size in weights]
        return weights

    def get_prices(self):
        clean_str = self.prices.strip("[]")
        str_list = clean_str.split(",")
        float_list = [float(num.strip()) for num in str_list if num.strip()]
        return float_list

    async def get_variants(self):
        variants = await self.get_weight_ids()
        for variant, p in zip(variants, self.get_prices()):
            variant["price"] = p
        return variants

    @classmethod
    @lru_cache
    def similar_details(cls):
        with open(base_dir / "db" / "attributes.json") as f:
            return json.load(f)

    async def create_item(self):
        snappshop = SnappShop()
        product: dict = await snappshop.create_product_quote(self)
        self.pid = product.get("data", {}).get("id")
        await snappshop.update_weights_options(self.pid, self)
        await snappshop.add_details(self.pid, self.similar_details())
        for i, im in enumerate(os.listdir(base_dir / "images" / self.image_dir)):
            await snappshop.add_image(
                self.pid, Path(base_dir / "images" / self.image_dir / im), i == 0
            )
        return await snappshop.submit(self.pid)

    async def add_item_to_shop(self):
        snappshop = SnappShop()
        shop_product: dict = await snappshop.add_to_shop(self.pid, self)
        self.shop_id = shop_product.get("data", {}).get("id")
        return shop_product

    async def process_item(self):
        try:
            await self.get_category()
            await self.get_brand()
            await self.get_size_ids()
            await self.get_color_ids()
            await self.get_weight_ids()
            c_rep = await self.create_item()
            # add_rep = await self.add_item_to_shop()
            self.done = True
            logging.info(f"Item {self.name_fa} added to shop {c_rep}")
        except Exception as e:
            logging.error(f"item {self.id}: {e}")


class SnappShop(metaclass=Singleton):
    def __init__(self, token=None):
        self.base_url = "https://apix.snappshop.ir"
        self.auth_url = f"{self.base_url}/auth/v1/password-login"
        self.vendor_id = "qJpOng"
        self.vendor_url = f"{self.base_url}/vendors/v1/{self.vendor_id}"
        self.catalog_url = f"{self.base_url}/catalog/v1"
        self.products_url = f"{self.base_url}/products/v1"
        self.categories_url = f"{self.base_url}/categories/v1"
        self.brands_url = f"{self.base_url}/brands/v1"
        self.token: JWT = JWT(token) if token else None
        self.session = aiohttp.ClientSession(headers=self.headers)

    def __repr__(self):
        return f"SnappShop({self.vendor_id})"

    async def close(self):
        await self.session.close()

    @property
    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
            "accept-language": "en,en-US;q=0.9,fa-IR;q=0.8,fa;q=0.7",
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

    async def request(
        self,
        method: str = "get",
        url: str = None,
        **kwargs,
    ):
        headers = kwargs.pop("headers", self.headers)
        async with self.session.request(
            method, url, headers=headers, **kwargs
        ) as response:
            if not response.ok:
                text = await response.json()
                logging.error(f"error text: {text}")
                response.raise_for_status()
            return await response.json()

    async def login(
        self, secret_file: Path = base_dir / "secrets" / "secret.json", **kwargs
    ):
        if self.token and not self.token.expired():
            return self.token

        with open(secret_file, "r") as f:
            secrets = json.load(f)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.auth_url, json=secrets, **kwargs) as response:
                response.raise_for_status()
                result = await response.json()

        self.token = JWT(result.get("data", {}).get("token"))
        global token
        token = self.token
        if self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.token

    @cache.file_cache()
    async def get_category(self, category_name, depth=1, id=None):
        params = {"depth": depth}
        if id:
            params["id"] = id
        categories: list[dict] = (
            await self.request(url=self.categories_url, params=params)
        ).get("data")
        for category in categories:
            if category.get("title") == category_name:
                return category
        return None

    @cache.file_cache()
    async def get_brand(self, brand_name):
        brands: list[dict] = (
            await self.request(url=self.brands_url, params={"query": brand_name})
        ).get("data")
        for brand in brands:
            if brand.get("title") == brand_name:
                return brand
        return None

    @cache.file_cache()
    async def seller_info(self, **kwargs):
        return await self.request(
            url=f"{self.base_url}/vendors/v1/seller-info", **kwargs
        )

    def option_key(self, weightOrSize="weight"):
        if weightOrSize == "weight":
            return "60rdDw"
        if weightOrSize == "size":
            return "lgwWgo"
        if weightOrSize == "color":
            return "60rdDw"
        raise ValueError("size and weight and color accepted")

    @cache.file_cache()
    async def options(self, page=1, weightOrSize="weight", **kwargs):
        # if weightOrSize == "weight":
        #     cid = kwargs.get("weight", "60rdDw")
        # else:
        #     cid = kwargs.get("size", "lgwWgo")
        cid = self.option_key(weightOrSize)
        return await self.request(
            url=f"{self.catalog_url}/attributes/{cid}/options",
            params={"page": page},
            **kwargs,
        )

    @cache.file_cache()
    async def all_options(self, weightOrSize="weight", **kwargs):
        options_data = []
        for p in range(1, 51):
            options = await self.options(page=p, weightOrSize=weightOrSize)
            if not options.get("data"):
                break
            options_data.extend(options.get("data"))
        return options_data

    @cache.file_cache()
    async def get_variants(self, option_list, weightOrSize="weight"):
        options_data = await self.all_options(weightOrSize=weightOrSize)
        found_options = []
        for op in options_data:
            for weight in option_list:
                if (
                    op.get("admin_name") == f"{weight}"
                    or op.get("admin_name") == f"{weight} گرم"
                ):
                    found_options.append(op)
        return [
            {"id": fo.get("id"), "value": fo.get("admin_name")} for fo in found_options
        ]

    async def create_product_quote(self, item: Item, **kwargs):
        json_data = {
            "step": "general",
            "category_id": item.category_id,
            "brand_id": item.brand_id,
            "is_original": True,
            "title": item.name_fa,
            "title_en": "",
            "description": item.description,
            "related_links": "",
            "type": "product",
        }

        return await self.request(
            method="post",
            url=f"{self.vendor_url}/product-quotes",
            json=json_data,
            **kwargs,
        )

    async def update_weights_options(self, pid, item, **kwargs):
        json_data = {
            "step": "variations",
            "variations": [
                {
                    "id": "lgwWgo",
                    "options": item.size_ids,
                },
                {
                    "id": "60rdDw",
                    "options": item.weight_ids,
                },
            ],
            "type": "product",
        }

        return await self.request(
            method="patch",
            url=f"{self.vendor_url}/product-quotes/{pid}",
            json=json_data,
            **kwargs,
        )

    async def add_details(self, pid, details: dict, **kwargs):
        json_data = details

        return await self.request(
            method="patch",
            url=f"{self.vendor_url}/product-quotes/{pid}",
            json=json_data,
            **kwargs,
        )

    async def add_image(self, pid, image_path: Path, is_main=False, **kwargs):
        mime_type, _ = mimetypes.guess_type(image_path)
        with aiohttp.MultipartWriter("form-data") as mp_writer:
            with open(image_path, "rb") as f:
                part = mp_writer.append(f)
                part.set_content_disposition(
                    "form-data", name="image", filename=image_path.name
                )
                part.headers["Content-Type"] = mime_type

                # Add the is_main field part
                is_main_part = mp_writer.append("true" if is_main else "false")
                is_main_part.set_content_disposition("form-data", name="is_main")

                headers = self.headers
                headers.update(mp_writer.headers)
                url = f"{self.vendor_url}/product-quotes/{pid}/images"

                return await self.request(
                    method="post",
                    url=url,
                    headers=headers,
                    data=mp_writer,
                    **kwargs,
                )

    async def submit(self, pid):
        return await self.request(
            "patch", f"{self.vendor_url}/product-quotes/{pid}/submit"
        )

    async def add_to_shop(self, pid, item: Item, **kwargs):
        variants = await item.get_variants()
        tasks = []
        for variant in variants:
            json_data = {
                "warranty_id": "x0QZq8",
                "lead_time": 1,  # how mant days
                "product_id": pid,  # "xdp2RP",
                "packaging_height": item.packaging_height,
                "packaging_length": item.packaging_length,
                "packaging_width": item.packaging_width,
                "packaging_weight": item.packaging_weight,
                "has_express_delivery": True,
                "variations": [
                    {
                        "attribute_id": self.option_key("weight"),
                        "attribute_value": variant["id"],
                    },
                ],
                "stock": 100,
                "price": int(variant["price"]),
                "capacity": 3,
            }

            tasks.append(
                self.request(
                    method="post",
                    url=f"{self.vendor_url}/inventory/products",
                    json=json_data,
                    **kwargs,
                )
            )

        results = []
        for task in tasks:
            results.append(await task)
            await asyncio.sleep(0.5)
        return results


def get_item(index=0) -> Item:
    df = excel.get_df()
    item = Item(df.loc[index].to_dict())
    return item


async def process_row(item: Item, sem=asyncio.Semaphore(4)):
    async with sem:
        if getattr(item, "done", False) and not pd.isna(item.done):
            return  # skip already done items
        await item.process_item()
        # update_sheet_row(index, item.__dict__)
        return item.__dict__


def get_token():
    if (base_dir / "secrets" / "token.json").exists():
        with open(base_dir / "secrets" / "token.json") as f:
            return json.load(f).get("token")


async def main():
    token = get_token()
    snappshop = SnappShop(token)
    await snappshop.login()
    df = excel.get_df()
    # item = Item(df.loc[0].to_dict())
    # sem = asyncio.Semaphore(4)
    # await process_row(item, sem)
    # r = await item.get_category()
    # print(r)
    # return
    sem = asyncio.Semaphore(4)

    tasks = []
    for i, row in df.iterrows():
        item = Item(row.to_dict())
        task = process_row(item, sem)
        tasks.append(task)

    rows = await asyncio.gather(*tasks)
    excel.update_excel(pd.DataFrame(rows))
    await snappshop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
