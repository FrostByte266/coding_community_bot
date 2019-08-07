FROM python:3.7

RUN pip install discord.py aiohttp networkx pandas matplotlib bs4 requests praw

COPY . .

CMD ["python", "main.py"]
