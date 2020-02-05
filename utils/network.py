# -*- coding: utf-8 -*-
"""
This software is licensed under the License (MIT) located at
https://github.com/ephreal/rollbot/Licence

Please see the license for any restrictions or rights granted to you by the
License.
"""


import aiohttp


async def fetch_page(url, headers={}):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url, headers)
        return html


async def fetch(session, url, headers):
    async with session.get(url, headers=headers) as html:
        return await html.text()
