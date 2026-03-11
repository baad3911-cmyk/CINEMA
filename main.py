import discord
from discord import app_commands
import os
import asyncio
import feedparser
import google.generativeai as genai
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

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
            for entry in feed.entries[:5]:
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
        except:
            continue
    return articles

def generate_tweet(article):
    prompt = f"You are a viral cinema Twitter account. Write a punchy English tweet about this movie news. Maximum 30 words. Strong opinion. Return ONLY the tweet text.\n\nTitle: {article['title']}\nSummary: {article['summary']}"
    response = model.generate_content(prompt)
    return response.text.strip()

async def send_daily_tweets():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    sent_today = False

    while not client.is_closed():
        now = datetime.now()
        if now.hour == 9 and now.minute == 0 and not sent_today:
            articles = get_top_articles()
            if articles and channel:
                import random
                selected = random.sample(articles, min(3, len(articles)))
                await channel.send("🎬 **Tes 3 tweets du jour !**")
                for i, article in enumerate(selected):
                    try:
                        tweet = generate_tweet(article)
                        embed = discord.Embed(
                            title=f"Tweet #{i+1}",
                            description=f"```{tweet}```",
                            color=0xe8c96d
                        )
                        embed.add_field(name="Source", value=article["source"], inline=True)
                        embed.add_field(name="Mots", value=str(len(tweet.split())) + "/30", inline=True)
                        embed.add_field(name="Article", value=article["title"][:80], inline=False)
                        if article.get("image"):
                            embed.set_image(url=article["image"])
                        await channel.send(embed=embed)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"Erreur: {e}")
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
    print(f"Bot connecte : {client.user}")
    client.loop.create_task(send_daily_tweets())

@tree.command(name="tweet", description="Genere un tweet maintenant")
async def tweet_now(interaction: discord.Interaction):
    await interaction.response.defer()
    articles = get_top_articles()
    if not articles:
        await interaction.followup.send("Impossible de recuperer les articles.")
        return
    import random
    article = random.choice(articles)
    tweet = generate_tweet(article)
    embed = discord.Embed(title="Tweet genere", description="```" + tweet + "```", color=0xe8c96d)
    embed.add_field(name="Source", value=article["source"], inline=True)
    embed.add_field(name="Mots", value=str(len(tweet.split())) + "/30", inline=True)
    embed.add_field(name="Article", value=article["title"][:80], inline=False)
    if article.get("image"):
        embed.set_image(url=article["image"])
    await interaction.followup.send(embed=embed)

client.run(os.environ["DISCORD_TOKEN"])
```

Ensuite ouvre `requirements.txt` et remplace par :
```
discord.py
feedparser
google-generativeai
