import os
import discord
import requests
import json
from discord.ext import commands
import random
from tenacity import retry, stop_after_attempt

from datetime import datetime




bot = commands.Bot(command_prefix='!')
bot.load_extension("cogs.musiccog")

now = datetime.now()
day = now.strftime("%A")



@bot.event
async def on_ready():
    print('Bot is ready and Running. the user is {0.user}'.format(bot))


@bot.command(name="quote")
async def get_quote(ctx):
    res = requests.get("https://animechan.vercel.app/api/random")
    data = json.loads(res.text)
    text = "**"+data["quote"]+"**"+ "\n" + "-" + data["character"] + "," + data["anime"]
    await ctx.send(text)


@bot.command(name="search")
async def get_anime_details(ctx,*,animeName):
  res = requests.get('https://api.jikan.moe/v3/search/anime?q=' + animeName)
  data = json.loads(res.text)
  info =  "Episode Count:" + str(data["results"][0]["episodes"]) + "\n" + "Airing Status:"+str(data["results"][0]["airing"])+"\n"+"Synopsis:" + data["results"][0]["synopsis"] + "\n" + "Rating:" + str(data["results"][0]["score"]) + "\n" + "Mal Link:" + data["results"][0]["url"]
  Embeds=discord.Embed(title="",color=0x00ff00)
  Embeds.set_thumbnail(url=data["results"][0]["image_url"])
  Embeds.add_field(name=data["results"][0]["title"],value=info, inline=True)
  await ctx.send(embed=Embeds)


    
@bot.command(name="schedule")

async def get_anime_schedule(ctx,days=day.lower()):
  days=days.lower()
  res = requests.get("https://api.jikan.moe/v3/schedule/" + days)
  data = json.loads(res.text)
  length = len(data[days])
  for i in range(length):
    text = "Title:" + data[days][i]["title"] + "\n" + "Link:" + data[days][i]["url"]
    await ctx.send(text)

def random_anime():
  ids=random.randint(1,8000)
  print(ids)
  res=requests.get("https://api.jikan.moe/v3/anime/"+str(ids))
  print(res.status_code)
  data = json.loads(res.text)
  arr=[]
  info="Episode Count:"+str(data["episodes"])+"\n"+"Airing Status:"+str(data["airing"])+"\n"+"Synopsis:"+data["synopsis"]+"\n"+"Score:"+str(data["score"]+"\n"+"Mal Link:"+data["url"])
  arr.append(data["title"])
  arr.append(info)
  arr.append(data["image_url"])
  return arr


@bot.command(name="random")

async def get_random_anime(ctx):
    arr=random_anime()
    print("here")
    Embeds=discord.Embed(title="",color=0x00ff00)
    Embeds.set_thumbnail(url=arr[2])
    Embeds.add_field(name=arr[0],value=arr[1], inline=True)
    await ctx.send(embed=Embeds)
    
    

    
bot.run(os.getenv("TOKEN"))