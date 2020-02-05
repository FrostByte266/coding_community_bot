# -*- coding: utf-8 -*-
"""
This software is licensed under the License (MIT) located at
https://github.com/ephreal/rollbot/Licence

Please see the license for any restrictions or rights granted to you by the
License.
"""


from discord.ext import commands
from utils import network

import json


class Joke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """
    Commands:
        .joke        - fetch a random dad joke
        .joke dad    - fetch a random dad joke
        .joke norris - fetch a random chuck norris joke
        .joke geek   - fetch a random geeky joke

    Methods:
        joke(ctx: discord context object, joke_type: string):
            The main command for this module. Returns various jokes as
            determined by the joke_type parameter. Currently accepted joke
            types are chuck, norris, and dad.

        chuck_norris_joke():
            -> joke: string
            Returns a string chuck norris joke.

        dad_joke():
            -> joke: string
            Returns a string dad joke
    """

    @commands.command(description="Get a random joke")
    async def joke(self, ctx, joke_type=None):
        """
        Fetches and displays a random joke for your amusement.

        Available joke types are
            chuck
            dad
            geek
            norris

        Get a random joke:
            .joke

        Get a dad joke:
            .joke dad

        Get a chuck norris joke:
            .joke chuck
        """

        if joke_type == "dad":
            return await ctx.send(await self.dad_joke())
        elif joke_type == "chuck" or joke_type == "norris":
            return await ctx.send(await self.chuck_norris_joke())
        elif joke_type == "geek":
            return await ctx.send(await self.geek_joke())

        return await ctx.send(await self.d_katz_joke_api())

    async def chuck_norris_joke(self):
        """
        Gets and returns a chuck norris joke.

            -> joke: string
        """

        url = "https://api.icndb.com/jokes/random"

        norris_joke = await network.fetch_page(url)
        norris_joke = json.loads(norris_joke)
        return norris_joke["value"]["joke"]

    async def dad_joke(self):
        """
        Gets and returns a dad joke from https://icanhazdadjoke.com

            -> joke: String
        """

        headers = {"Accept": "application/json"}
        url = "https://icanhazdadjoke.com"
        dad_joke = await network.fetch_page(url, headers)
        dad_joke = json.loads(dad_joke)
        return dad_joke["joke"]

    async def geek_joke(self):
        """
        Gets and returns a random joke from
        https://geek-jokes.sameerkumar.website/api

            -> joke: String
        """

        headers = {"Accept": "application/json"}
        url = "https://geek-jokes.sameerkumar.website/api"
        geek_joke = await network.fetch_page(url, headers=headers)
        return geek_joke

    async def d_katz_joke_api(self):
        """
        Gets and returns a joke from the joke database maintained by 15DKatz
        at https://official-joke-api.appspot.com/random_joke

            -> joke: String
        """

        url = "https://official-joke-api.appspot.com/random_joke"
        random_joke = await network.fetch_page(url)
        random_joke = json.loads(random_joke)
        return f"{random_joke['setup']}\n{random_joke['punchline']}"


def setup(bot):
    bot.add_cog(Joke(bot))
