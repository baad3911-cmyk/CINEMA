import discord
from discord import app_commands
import os
import asyncio
import feedparser
from groq import Groq
from datetime import datetime
import random

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

CHANNEL_ID = int(os.environ["CHANNEL_ID"])

RSS_FEEDS = [
    "https://deadline.com/feed/",
    "https://variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://collider.com/feed/",
    "https://screenrant.com/feed/",
]

def get_top_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:300]
                image = None
                if "media_thumbnail" in entry:
                    image = entry.media_thumbnail[0].get("url")
                elif "media_content" in entry:
                    image = entry.media_content[0].get("url")
                articles.append({
                    "title": title,
                    "summary": summary,
                    "source": feed.feed.get("title", ""),
                    "image": image
                })
        except Exception as e:
            print("Feed error: " + str(e))
            continue
    return articles

def generate_tweet(article):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a viral cinema Twitter account. Write a punchy English tweet about this week movie news. Maximum 15 words. Very short and punchy. Return ONLY the tweet text, nothing else."
            },
            {
                "role": "user",
                "content": "Title: " + article["title"] + "\nSummary: " + article["summary"]
            }
        ],
        max_tokens=60
    )
    return response.choices[0].message.content.strip()

async def send_daily_tweets():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    sent_today = False

    while not client.is_closed():
        now = datetime.now()
        if now.hour == 9 and now.minute == 0 and not sent_today:
            articles = get_top_articles()
            if articles and channel:
                selected = random.sample(articles, min(3, len(articles)))
                await channel.send("Tes 3 tweets du jour sont arrives !")
                for i, article in enumerate(selected):
                    try:
                        tweet = generate_tweet(article)
                        embed = discord.Embed(
                            title="Tweet #" + str(i+1),
                            description="```" + tweet + "```",
                            color=0xe8c96d
                        )
                        embed.add_field(name="Source", value=article["source"], inline=True)
                        embed.add_field(name="Mots", value=str(len(tweet.split())) + "/15", inline=True)
                        embed.add_field(name="Article", value=article["title"][:80], inline=False)
                        if article.get("image"):
                            embed.set_image(url=article["image"])
                        await channel.send(embed=embed)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print("Erreur tweet: " + str(e))
            sent_today = True
            await asyncio.sleep(60)
        elif now.hour == 10:
            sent_today = False
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(30)

@client.event
async def on_ready():
    await tree.sync()
    print("Bot connecte : " + str(client.user))
    client.loop.create_task(send_daily_tweets())

@tree.command(name="tweet", description="Genere un tweet maintenant")
async def tweet_now(interaction: discord.Interaction):
    await interaction.response.defer()
    articles = get_top_articles()
    if not articles:
        await interaction.followup.send("Impossible de recuperer les articles.")
        return
    article = random.choice(articles)
    tweet = generate_tweet(article)
    embed = discord.Embed(
        title="Tweet genere",
        description="```" + tweet + "```",
        color=0xe8c96d
    )
    embed.add_field(name="Source", value=article["source"], inline=True)
    embed.add_field(name="Mots", value=str(len(tweet.split())) + "/15", inline=True)
    embed.add_field(name="Article", value=article["title"][:80], inline=False)
    if article.get("image"):
        embed.set_image(url=article["image"])
    await interaction.followup.send(embed=embed)

client.run(os.environ["DISCORD_TOKEN"])
