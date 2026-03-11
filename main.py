import discord
from discord import app_commands
import anthropic
import os
import asyncio
import feedparser
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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
                articles.append({"title": title, "summary": summary, "source": feed.feed.get("title", "")})
        except:
            continue
    return articles[:9]

def generate_tweet(article):
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        system="You are a viral cinema Twitter account. Write a punchy English tweet about this movie news. Maximum 30 words. Strong opinion. Return ONLY the tweet text, nothing else.",
        messages=[{"role": "user", "content": f"Title: {article['title']}\nSummary: {article['summary']}"}]
    )
    return message.content[0].text.strip()

async def send_daily_tweets():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    
    SEND_HOURS = [9, 15, 21]
    
    while not client.is_closed():
        now = datetime.now()
        if now.hour in SEND_HOURS and now.minute == 0:
            articles = get_top_articles()
            if articles and channel:
                import random
                selected = random.sample(articles, min(3, len(articles)))
                for i, article in enumerate(selected):
                    try:
                        tweet = generate_tweet(article)
                        embed = discord.Embed(
                            title=f"🎬 Tweet #{i+1} — {now.strftime('%H:%M')}",
                            description=f"```{tweet}```",
                            color=0xe8c96d
                        )
                        embed.add_field(name="Source", value=article["source"], inline=True)
                        embed.add_field(name="Mots", value=str(len(tweet.split())) + "/30", inline=True)
                        embed.add_field(name="Article", value=article["title"][:80], inline=False)
                        await channel.send(embed=embed)
                        await asyncio.sleep(5)
                    except Exception as e:
                        print(f"Erreur: {e}")
            await asyncio.sleep(60)
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
    await interaction.followup.send(embed=embed)

client.run(os.environ["DISCORD_TOKEN"])
```

---

Ensuite crée un 2ème fichier dans GitHub nommé `requirements.txt` avec :
```
discord.py
anthropic
feedparser
