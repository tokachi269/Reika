'''Reika (Discord BOT for Steam Workshop modders)

https://github.com/takana-v/Reika
'''
import datetime
import re
import sys
import unicodedata

from dateutil.parser import parse
import discord
import lxml.html
from pandas import read_pickle,to_pickle
import pytz
import requests
import urllib.parse

__version__ = '1.0.0'
sv_setting = read_pickle('setting.pkl')
server_admin = 473143965923934220

# search_cmd (s/author word)
def search_author(url,word):
    html = lxml.html.fromstring(requests.get(url).text)
    ws_index = {}
    for i in range(len(html.xpath('//div[contains(@class,"workshopItemTitle")]'))):
        ws_index[str(html.xpath('//div[contains(@class,"workshopItemTitle")]/..')[i].attrib["href"])] = str(html.xpath('//div[@class="workshopItemAuthorName"]/a')[i].text_content())
    for v in ws_index.values():
        if word.lower() in v.lower():
            result = v
            break
    else:
        return None
    return [k for k, v in ws_index.items() if v == result][0]

# search_cmd (s/ word)
def search_url(url):
    html = lxml.html.fromstring(requests.get(url).text)
    try:
        return str(html.xpath('//div[contains(@class,"workshopItemTitle")]/..')[0].attrib["href"])
    except:
        return None

def get_last_update(posted_time):
    updated_time_status = (int(datetime.datetime.now().timestamp())-posted_time) // 86400
    if updated_time_status == 0:
        updated_time_status = 'Today :new:'
    elif updated_time_status == 1:
        updated_time_status = 'Yesterday :new:'
    elif 1 < updated_time_status < 5:
        updated_time_status = str(updated_time_status)+' days ago :new:'
    else:
        updated_time_status = str(updated_time_status)+' days ago'
    return updated_time_status

def screenshots_description(html):
    try:
        description = str(html.xpath('//div[@class="screenshotAuthorSays"]')[0].text_content())
        try:
            description = description + ' | ' + str(html.xpath('//div[@class="screenshotDescription"]')[0].text_content())
        except:
            pass
    except:
        try:
            description = str(html.xpath('//div[@class="screenshotDescription"]')[0].text_content())
        except:
            description = 'No description'
    return count_str(description)

def images_description(html):
    try:
        description = str(html.xpath('//div[@class="nonScreenshotDescription"]')[0].text_content())
        if not description:
            raise Exception
    except:
        description = 'No description'
    return count_str(description)

def workshop_description(html):
    try:
        description = str(html.xpath('//div[@class="workshopItemDescription"]')[0].text_content())
        if not description:
            raise Exception
    except:
        description = 'No description'
    return count_str(description)

def guide_description(html):
    try:
        description = str(html.xpath('//div[@class="guideTopDescription"]')[0].text_content())
        if not description:
            raise Exception
    except:
        description = 'No description'
    return count_str(description)

def get_workshop_common_data(html):
    file_size = str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[0].text_content())
    posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[1].text_content()).replace('@','')))
    return file_size,posted_time

def get_author_data(html):
    author_name = str(html.xpath('//div[@class="friendBlockContent"]')[0].text_content()).replace(str(html.xpath('//div[@class="friendBlockContent"]/span')[0].text_content()),'').strip()
    author_url = str(html.xpath('//a[@class="friendBlockLinkOverlay"]')[0].attrib['href'])
    author_icon = str(html.xpath('//div[@class="creatorsBlock"]//div[contains(@class,"playerAvatar")]/img')[0].attrib['src'])
    return author_name,author_url,author_icon

def get_workshop_thumbnail(html):
    try:
        thumbnail = str(html.xpath('//img[@id="previewImageMain"]')[0].attrib['src'])
        if not thumbnail:
            raise Exception
    except:
        try:
            thumbnail = str(html.xpath('//img[@class="workshopItemPreviewImageEnlargeable"]')[0].attrib['src'])
            if not thumbnail:
                raise Exception
        except:
            thumbnail = 'https://reika.invalid/thumbnail.jpg'
    return thumbnail

def get_workshop_tag(html):
    tag = ''
    col_right= lxml.html.fromstring(lxml.html.tostring(html.xpath('//div[@class="col_right"]/div[@class="rightDetailsBlock"]')[0])).xpath('//a')
    for i in range(len(col_right)):
        tag = tag +' '+ str(col_right[i].text_content())
    if not tag:
        tag = 'No tag'
    return tag

def count_str(description):
    description_text = ''
    width = 0
    for i in description:
        if re.fullmatch(r'F|W|A',unicodedata.east_asian_width(i)):
            width += 2
        else:
            width += 1
        if width > 190:
            description_text = description_text+'...'
            break
        description_text = description_text + str(i)
    return description_text

def get_guide_tag(html):
    tag = ''
    for i in range(len(html.xpath('//div[@class="workshopTags"]/a'))-1):
        tag = tag +' '+ str(html.xpath('//div[@class="workshopTags"]/a')[i].text_content())
    if not tag:
        tag = 'No tag'
    return tag

def workshop_collection_thumbnail(html):
    try:
        thumbnail = str(html.xpath('//img[@class="collectionBackgroundImage"]')[0].attrib['src'])
        if not thumbnail:
            raise Exception
    except:
        thumbnail = 'https://reika.invalid/thumbnail.jpg'
    return thumbnail

def discussion(url):
    html = lxml.html.fromstring(requests.get(url).text)
    if url[-1] == '/':
        forum_id = str(url.split('/')[-2])
    else:
        forum_id = str(url.split('/')[-1])
    description = count_str(html.xpath('//*[@id="forum_op_'+forum_id+'"]/div[4]/text()')[0].strip())
    author_name = html.xpath('//*[@id="forum_op_'+forum_id+'"]/div[2]/a/text()')[0].strip()
    author_icon = html.xpath('//*[@id="forum_op_'+forum_id+'"]/div[1]/a/img')[0].attrib["src"]
    author_url = html.xpath('//*[@id="forum_op_'+forum_id+'"]/div[1]/a')[0].attrib["href"]
    title = html.xpath('//*[@id="forum_op_'+forum_id+'"]/div[3]/text()')[0].strip()
    thumbnail = 'https://reika.invalid/thumbnail.jpg'
    posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//*[@id="AppHubContent"]/div/div[2]/div[2]/div/div[1]/span[2]')[0].text_content()).replace('@','')))
    posts_count = str(html.xpath('//*[@id="AppHubContent"]/div/div[2]/div[2]/div/div[2]/span[2]')[0].text_content())
    return {
        "title":title,
        "url":url,
        "description":description,
        "timestamp":posted_time,
        "author":{
            "url":author_url,
            "name":author_name,
            "icon_url":author_icon
        },
        "thumbnail":thumbnail,
        "field":{
            "field1":{
                "name":"Posts : "+posts_count ,
                "value":":date: "+str(posted_time),
                "inline":True
            }
        },
        "footer":"no tag"
    }


def workshop(url):
    html = lxml.html.fromstring(requests.get(url).text)
    page_type = str(html.xpath("//a[contains(@class,'apphub_sectionTab active ')]")[0].attrib['href']).split('/')[-2]
    if page_type == 'screenshots' or page_type == 'images':
        try:
            title = str(html.xpath('//div[@class="workshopItemTitle"]')[0].text_content())
            if not title:
                raise Exception
        except:
            title = str(html.xpath('//title')[0].text_content())
        if page_type == 'screenshots':
            description = screenshots_description(html)
        else:
            description = images_description(html)
        thumbnail = str(html.xpath('//img[@id="ActualMedia"]')[0].attrib['src'])
        votes_up = str(html.xpath('//span[@id="VotesUpCount"]')[0].text_content())
        visitors = str(html.xpath('//table[@class="stats_table"]//td')[0].text_content())
        favorites = str(html.xpath('//table[@class="stats_table"]//td')[2].text_content())
        file_size,posted_time = get_workshop_common_data(html)
        author_name,author_url,author_icon = get_author_data(html)
        update_status = get_last_update(int(posted_time.timestamp()))
        return {
            "title":title,
            "url":url,
            "description":description,
            "timestamp":posted_time,
            "author":{
                "url":author_url,
                "name":author_name,
                "icon_url":author_icon
            },
            "thumbnail":thumbnail,
            "field":{
                "field1":{
                    "name":":thumbsup: **"+votes_up+"**",
                    "value":":hearts: **"+favorites+"** :eye: **"+visitors+"**",
                    "inline":True
                },
                "field2":{
                    "name":":file_folder: **`"+file_size+"`**",
                    "value":":tools: Last update: "+update_status,
                    "inline":True
                }
            },
            "footer":"No tag"
        }

    if page_type == 'workshop':
        if html.xpath('//div[@class="collectionNotifications"]'):
            title = str(html.xpath('//div[@class="workshopItemTitle"]')[0].text_content())
            description = workshop_description(html)
            thumbnail = workshop_collection_thumbnail(html)
            visitors = str(html.xpath('//*[@id="rightContents"]/div[2]/div[1]/div/div[1]/div[1]')[0].text_content())
            favorites = str(html.xpath('//*[@id="rightContents"]/div[2]/div[1]/div/div[1]/div[2]')[0].text_content())
            author_link = html.xpath('//div[@class="linkAuthor"]/a')[0]
            author_name = str(author_link.text_content())
            author_url = str(author_link.attrib["href"])
            try:
                author_icon = str(html.xpath('//*[@id="rightContents"]/div[1]/div[2]/div[2]/div/div/div[1]/div/div/a/img')[0].attrib["src"])
            except:
                author_icon = str(html.xpath('//*[@id="rightContents"]/div[1]/div/div[2]/div/div/div[1]/div/div/a/img')[0].attrib['src'])
            try:
                posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//*[@id="rightContents"]/div[2]/div[4]/div/div[2]/div[1]')[0].text_content()).replace('@','')))
                try:
                    updated_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//*[@id="rightContents"]/div[2]/div[4]/div/div[2]/div[2]')[0].text_content()).replace('@','')))
                except:
                    updated_time = posted_time
            except:
                posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//*[@id="rightContents"]/div[2]/div[3]/div/div[2]/div[1]')[0].text_content()).replace('@','')))
                try:
                    updated_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//*[@id="rightContents"]/div[2]/div[3]/div/div[2]/div[2]')[0].text_content()).replace('@','')))
                except:
                    updated_time = posted_time
            update_status = get_last_update(int(updated_time.timestamp()))
            return {
                "title":title,
                "url":url,
                "description":description,
                "timestamp":posted_time,
                "author":{
                    "url":author_url,
                    "name":author_name,
                    "icon_url":author_icon
                },
                "thumbnail":thumbnail,
                "field":{
                    "field1":{
                        "name":":hearts: **"+favorites+"** :eye: **"+visitors+"**",
                        "value":":tools: Last update: "+update_status,
                        "inline":True
                    }
                },
                "footer":'No tag'
            }
        else:
            title = str(html.xpath('//div[@class="workshopItemTitle"]')[0].text_content())
            description = workshop_description(html)
            thumbnail = get_workshop_thumbnail(html)
            visitors = str(html.xpath('//table[@class="stats_table"]//td')[0].text_content())
            subscribe = str(html.xpath('//table[@class="stats_table"]//td')[2].text_content())
            favorites = str(html.xpath('//table[@class="stats_table"]//td')[4].text_content())
            file_size,posted_time = get_workshop_common_data(html)
            author_name,author_url,author_icon = get_author_data(html)
            try:
                updated_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[2].text_content()).replace('@','')))
            except:
                updated_time = posted_time
            update_status = get_last_update(int(updated_time.timestamp()))
            tag = get_workshop_tag(html)
            return {
                "title":title,
                "url":url,
                "description":description,
                "timestamp":posted_time,
                "author":{
                    "url":author_url,
                    "name":author_name,
                    "icon_url":author_icon
                },
                "thumbnail":thumbnail,
                "field":{
                    "field1":{
                        "name":":white_check_mark: **"+subscribe+"**",
                        "value":":hearts: **"+favorites+"** :eye: **"+visitors+"**",
                        "inline":True
                    },
                    "field2":{
                        "name":":file_folder: **`"+file_size+"`**",
                        "value":":tools: Last update: "+update_status,
                        "inline":True
                    }
                },
                "footer":tag
            }
    if page_type == 'videos':
        try:
            title = str(html.xpath('//div[@class="workshopItemTitle"]')[0].text_content())
            if not title:
                raise Exception
        except:
            title = str(html.xpath('//title')[0].text_content())
        description = images_description(html)
        thumbnail = str(html.xpath('//meta[@property="og:image"]')[0].attrib['content'])
        votes_up = str(html.xpath('//span[@id="VotesUpCount"]')[0].text_content())
        common_data = html.xpath('//table[@class="stats_table"]//td')
        views = str(common_data[0].text_content())
        visitors = str(common_data[2].text_content())
        favorites = str(common_data[4].text_content())
        author_name,author_url,author_icon = get_author_data(html)
        posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[0].text_content()).replace('@','')))
        update_status = get_last_update(int(posted_time.timestamp()))
        return {
            "title":title,
            "url":url,
            "description":description,
            "timestamp":posted_time,
            "author":{
                "url":author_url,
                "name":author_name,
                "icon_url":author_icon
                },
            "thumbnail":thumbnail,
            "field":{
                "field1":{
                    "name":":thumbsup: **"+votes_up+"**",
                    "value":":hearts: **"+favorites+"** :eye: **"+visitors+"**",
                    "inline":True
                    },
                "field2":{
                    "name":":arrow_forward: **"+views+"**",
                    "value":":tools: Last update: "+update_status,
                    "inline":True
                    }
                },
            "footer":"No tag"
        }
    if page_type == 'guides':
        try:
            title = str(html.xpath('//div[@class="workshopItemTitle"]')[0].text_content())
            if not title:
                raise Exception
        except:
            title = str(html.xpath('//title')[0].text_content())
        description = guide_description(html)
        thumbnail = str(html.xpath('//div[@class="guidePreviewImage"]//img')[0].attrib['src'])
        common_data = html.xpath('//table[@class="stats_table"]//td')
        visitors = str(common_data[0].text_content())
        favorites = str(common_data[2].text_content())
        author_name,author_url,author_icon = get_author_data(html)
        posted_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[0].text_content()).replace('@','')))
        try:
            updated_time = pytz.timezone('America/Los_Angeles').localize(parse(str(html.xpath('//div[@class="detailsStatsContainerRight"]/div[@class="detailsStatRight"]')[1].text_content()).replace('@','')))
        except:
            updated_time = posted_time
        update_status = get_last_update(int(updated_time.timestamp()))
        tag = get_guide_tag(html)
        return {
            "title":title,
            "url":url,
            "description":description,
            "timestamp":posted_time,
            "author":{
                "url":author_url,
                "name":author_name,
                "icon_url":author_icon
            },
            "thumbnail":thumbnail,
            "field":{
                "field1":{
                    "name":":hearts: **"+favorites+"** :eye: **"+visitors+"**",
                    "value":":tools: Last update: "+update_status,
                    "inline":True
                }
            },
            "footer":tag
        }

def check_url(url):
    if re.fullmatch(r'https://steamcommunity.com/sharedfiles/filedetails/\?id=[0-9]+.*',url):
        return workshop(url)
    if re.fullmatch(r'https://steamcommunity.com/workshop/filedetails/\?id=[0-9]+.*',url):
        return workshop(url)
    elif re.fullmatch(r'https://steamcommunity.com/app/[0-9]+/discussions/[0-9]+/[0-9]+/*',url):
        return discussion(url)
    else:
        return None

def main(token):
    client = discord.Client()

    @client.event
    async def on_ready():
        pass

    @client.event
    async def on_message(message):
        if str(message.channel.type) != 'text':
            return

        if message.content == "r/stop" and message.author.id == server_admin:
            exit()

        elif str(client.user.id) in message.content and sv_setting[message.guild.id]['csljp'] == 1:
            if ':peropero:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif 'ペロペロ' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif 'ぺろぺろ' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':peroperov:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':peroperoh:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':ashi_asi:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':oppai:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':eroi:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':chin_tin::chin_tin:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':chin_tin::ko:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':chin_tin: :chin_tin:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif ':chin_tin: :ko:' in message.content:
                await message.channel.send(f'{message.author.mention} 二度とわたしに話しかけないで')
            elif 'かわいい' in message.content:
                await message.channel.send(f'{message.author.mention} 知ってる。')
            elif ':kawaii:' in message.content:
                await message.channel.send(f'{message.author.mention} 知ってる。')
            elif '意気込み' in message.content:
                await message.channel.send(f'{message.author.mention} あんたには負けないんだから')

        elif message.content.startswith('r/set-gameid'):
            if message.author.id != server_admin and message.author.id != message.guild.owner_id:
                return
            try:
                sv_setting.update({message.guild.id:{'gameid':str(int(message.content.split(' ')[1])),'csljp':sv_setting[message.guild.id]['csljp']}})
            except:
                try:
                    sv_setting.update({message.guild.id:{'gameid':str(int(message.content.split(' ')[1]))}})
                except:
                    return
            to_pickle(sv_setting,'setting.pkl')
            await message.channel.send('[OK] gameid = '+str(message.content.split(' ')[1]))

        elif message.content.startswith('r/set-csljp'):
            if message.author.id != server_admin and message.author.id != message.guild.owner_id:
                return
            try:
                sv_setting.update({message.guild.id:{'gameid':sv_setting[message.guild.id]['gameid'],'csljp':int(message.content.split(' ')[1])}})
            except:
                try:
                    sv_setting.update({message.guild.id:{'csljp':int(message.content.split(' ')[1])}})
                except:
                    return
            to_pickle(sv_setting,'setting.pkl')
            await message.channel.send('[OK] csljp = '+str(message.content.split(' ')[1]))

        elif message.content.startswith('r/view-setting'):
            if message.author.id != server_admin and message.author.id != message.guild.owner_id:
                return
            try:
                await message.channel.send(str(sv_setting[message.guild.id]))
            except:
                await message.channel.send('Not found / 設定がありません。')

        elif message.content == ('r/help'):
            embed = discord.Embed()
            embed.add_field(name='s/ word',value='search on steam/steamを検索します', inline=False)
            embed.add_field(name='s/author word',value='search on steam (narrow the results by author)/steamを検索します(作成者を指定)', inline=False)
            if message.author.id == server_admin or message.author.id == message.guild.owner_id:
                embed.add_field(name='r/set-gameid',value='You can get gameid on url of storepage. e.g.(Cities:Skylines) r/set-gameid 255710', inline=False)
                embed.add_field(name='r/set-csljp',value='0 or 1 (Default:0)', inline=False)
            embed.set_footer(text='Reika ver '+str(__version__))
            await message.channel.send(embed=embed)


        elif message.content.startswith('s/'):
            raw_searchtext = message.content.split(' ')
            if len(raw_searchtext) == 1:
                return
            searchtext = ''
            for i in range(1,len(raw_searchtext)):
                searchtext = searchtext+urllib.parse.quote(str(raw_searchtext[i]))+'+'
            try:
                steam_url = 'https://steamcommunity.com/workshop/browse/?appid='+str(sv_setting[message.guild.id]['gameid'])+'&searchtext='+searchtext[:-1]
            except:
                await message.channel.send('`r/set-gameid`コマンドを使用してゲームIDをセットしてください。')
                return
            if raw_searchtext[0] == 's/':
                search_result = search_url(steam_url)
                if search_result is None:
                    try:
                        if sv_setting[message.guild.id]['csljp'] == 1:
                            await message.channel.send('結果が見つからなかった...')
                        else:
                            await message.channel.send('見つかりませんでした。/ Not found')
                        return
                    except:
                        await message.channel.send('見つかりませんでした。/ Not found')
                        return
                else:
                    await message.channel.send(search_result)
            else:
                search_result = search_author(steam_url,raw_searchtext[0][2:])
                if search_result is None:
                    try:
                        if sv_setting[message.guild.id]['csljp'] == 1:
                            await message.channel.send('結果が見つからなかった...')
                        else:
                            await message.channel.send('見つかりませんでした。/ Not found')
                        return
                    except:
                        await message.channel.send('見つかりませんでした。/ Not found')
                        return
                else:
                    await message.channel.send(search_result)

        else:
            message_text = message.content.replace('\n',' ').replace('　',' ').split(' ')
            for i in message_text:
                result = check_url(i)
                if result is None:
                    pass
                else:
                    embed = discord.Embed(title=result['title'],url=result['url'],description=result['description'], timestamp=result['timestamp'])
                    embed.set_author(url=result['author']['url'], name=result['author']['name'],icon_url=result['author']['icon_url'])
                    embed.set_thumbnail(url=result['thumbnail'])
                    for i in range(1,len(result['field'])+1):
                        embed.add_field(name=result['field']['field'+str(i)]['name'],value=result['field']['field'+str(i)]['value'], inline=result['field']['field'+str(i)]['inline'])
                    embed.set_footer(text=result['footer'])
                    await message.channel.send(embed=embed)

    client.run(token)

if __name__ == '__main__':
    main(sys.argv[1])
