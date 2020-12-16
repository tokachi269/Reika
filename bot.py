'''Reika (Discord BOT for Steam Workshop modders)

https://github.com/takana-v/Reika
'''
import asyncio
import datetime
import random
import re
import sys
import unicodedata

import json
import traceback
import discord
import pytz
import requests
import urllib.parse

__version__ = '2.0.1'
setting = {}

# Defines
class STANDARD_RETURN:
    OK = 0
    NOT_OK = 1
    FATAL_ERROR = 2

class TALK_RETURN:
    NO = 0
    DT = 1
    TSUN = 2
    OTHER = 3
    IKIGOMI = 4

# reika管理者のdiscordユーザーID
# このユーザーとサーバーオーナーのみが設定できる
server_admin = 000000000000000000
org_master = 000000000000000000 # 作成者のID

def read_setting():
    """
    jsonファイルの設定を読み取り

    Returns
    ----------
    (return_0) : int
        STANDARD_RETURNクラス参照
    (return_1) : dict
        設定内容
    """
    try:
        with open('settings.json','r') as f:
            return STANDARD_RETURN.OK,json.load(f)
    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK,{}

def write_setting(data):
    """
    jsonファイルに設定を書き出し

    Returns
    ----------
    (return) : int
        STANDARD_RETURNクラス参照
    """
    try:
        with open('settings.json','w') as f:
            json.dump(data,f)
        return STANDARD_RETURN.OK
    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK

def talk(word):
    """
    たまに送られてくるreikaへの雑談を判定

    Parameters
    ----------
    word : str
        判定する内容

    Returns
    ----------
    (return) : int
        他クラス参照
    """
    # 卑猥と判定するワード
    words_dic_1 = ['peropero','ペロペロ','ぺろぺろ','ashi_asi','oppai','おっぱい','eroi','エロ','chin_tin']
    for i in words_dic_1:
        # 一つづつチェック
        if i in word:
            return TALK_RETURN.DT

    # スタンプで卑猥な言葉をかける紳士を判定
    if re.fullmatch(r'.*:chin_tin:.*(:chin_tin:)|(:ko:).*',word):
        return TALK_RETURN.DT

    # reikaをほめる言葉リスト
    words_dic_2 = ['kawaii','かわいい','可愛い']
    for i in words_dic_2:
        # （自分の名前）かわいいと言ってreikaに「かわいい」と言わせようとする紳士を判定
        # 文中にreikaが入っていないと「ん？」と返す（はず）
        # どうやって動いているのか分からないけど動いているのでOK
        if i in word:
            name_check = word.split(i)[0]
            for i2 in ['Reika','reika','Reika_','Reika_r','れいか','レイカ']:
                if i2 in name_check:
                    return TALK_RETURN.TSUN
            if re.fullmatch(r'<@\d+>\s*',name_check):
                return TALK_RETURN.TSUN

            return TALK_RETURN.OTHER

    if '意気込み' in word:
        return TALK_RETURN.IKIGOMI

    return TALK_RETURN.NO

def get_contentdetail(cont_id,steam_key):
    """
    IDに紐づけられたアイテムの詳細を取得

    Parameters
    ----------
    cont_id : str
        コンテンツID
    steam_key : str
        steamAPIアクセスキー

    Returns
    ----------
    (return_0) : int
        STANDARD_RETURNクラス参照
    (return_1) : dict
        各種情報
    """
    try:
        api_res = requests.post('https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/',data={'itemcount':1,'publishedfileids[0]':cont_id})
        if api_res.status_code != requests.codes.ok:
            raise Exception
        cont = api_res.json()['response']

        # 写真とかの場合終了しようと考えたけどいったん保留
        '''
        if cont['publishedfiledetails'][0]['filename'] != '':
            raise Exception
        elif cont['publishedfiledetails'][0]['title'] == '':
            raise Exception
        elif cont['publishedfiledetails'][0]['preview_url'] == '':
            raise Exception
        elif int(cont['publishedfiledetails'][0]['file_size']) == 0:
            raise Exception
        '''

        # レスポンスから各種情報取得
        title = cont['publishedfiledetails'][0]['title']
        url = 'https://steamcommunity.com/sharedfiles/filedetails/?id=' + cont_id
        description = count_str(to_markdown(cont['publishedfiledetails'][0]['description']))
        timestamp = cont['publishedfiledetails'][0]['time_updated']
        author_id = str(cont['publishedfiledetails'][0]['creator'])
        thumbnail = cont['publishedfiledetails'][0]['preview_url']
        update_status = get_last_update(timestamp)
        file_size = byte_unit(int(cont['publishedfiledetails'][0]['file_size']))
        subscribe = '{:,}'.format(cont['publishedfiledetails'][0]['subscriptions'])
        favorites = '{:,}'.format(cont['publishedfiledetails'][0]['favorited'])
        visitors = '{:,}'.format(cont['publishedfiledetails'][0]['views'])
        tag = ''
        for tag_dict in cont['publishedfiledetails'][0]['tags']:
            try:
                tag = tag + tag_dict['tag'] + ', '
            except Exception:
                pass
        else:
            if len(cont['publishedfiledetails'][0]['tags']) > 0:
                tag = tag[:-2]

        # 製作者の情報取得
        author_api_res = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={0}&steamids={1}'.format(steam_key,author_id))
        if author_api_res.status_code != requests.codes.ok:
            raise Exception
        a_cont = author_api_res.json()['response']
        author_url = a_cont['players'][0]['profileurl']
        author_name = a_cont['players'][0]['personaname']
        author_icon = a_cont['players'][0]['avatar']

        return STANDARD_RETURN.OK, {
            "title":title,
            "url":url,
            "description":description,
            "timestamp":datetime.datetime.fromtimestamp(timestamp,tz=pytz.timezone('UTC')),
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

    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK, {}


def searchitem(search_word,steam_key,app_id,check_author=False,author_name=''):
    """
    ワードに応じた作品の情報を表示

    Parameters
    ----------
    search_word : list
        コンテンツID
    steam_key : str
        steamAPIアクセスキー

    Returns
    ----------
    (return_0) : int
        STANDARD_RETURNクラス参照
    (return_1) : dict
        各種情報
    """
    try:
        searchtext = ''
        for w in search_word:
            searchtext = searchtext + urllib.parse.quote(str(w)) + '+'
        api_res = requests.get('https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/?key={0}&appid={1}&search_text={2}&return_tags=true&query_type=3&days=180'.format(steam_key,app_id,searchtext[:-1]))
        # 関連性
        # api_res = requests.get('https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/?key={0}&appid={1}&search_text={2}&return_tags=true&query_type=12'.format(steam_key,app_id,searchtext[:-1]))
        if api_res.status_code != requests.codes.ok:
            raise Exception
        cont = api_res.json()['response']
        if len(cont['publishedfiledetails']) == 0:
            raise Exception

        title = cont['publishedfiledetails'][0]['title']
        url = 'https://steamcommunity.com/sharedfiles/filedetails/?id=' + str(cont['publishedfiledetails'][0]['publishedfileid'])
        description = count_str(to_markdown(cont['publishedfiledetails'][0]['file_description']))
        timestamp = cont['publishedfiledetails'][0]['time_updated']
        thumbnail = cont['publishedfiledetails'][0]['preview_url']
        subscribe = '{:,}'.format(cont['publishedfiledetails'][0]['subscriptions'])
        favorites = '{:,}'.format(cont['publishedfiledetails'][0]['favorited'])
        visitors = '{:,}'.format(cont['publishedfiledetails'][0]['views'])
        file_size = byte_unit(int(cont['publishedfiledetails'][0]['file_size']))
        update_status = get_last_update(timestamp)
        author_id = cont['publishedfiledetails'][0]['creator']

        tag = ''
        for tag_dict in cont['publishedfiledetails'][0]['tags']:
            try:
                tag = tag + tag_dict['tag'] + ', '
            except Exception:
                pass
        else:
            if len(cont['publishedfiledetails'][0]['tags']) > 0:
                tag = tag[:-2]

        author_api_res = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={0}&steamids={1}'.format(steam_key,author_id))
        if author_api_res.status_code != requests.codes.ok:
            raise Exception
        a_cont = author_api_res.json()['response']
        author_url = a_cont['players'][0]['profileurl']
        author_name = a_cont['players'][0]['personaname']
        author_icon = a_cont['players'][0]['avatar']

        return STANDARD_RETURN.OK, {
            "title":title,
            "url":url,
            "description":description,
            "timestamp":datetime.datetime.fromtimestamp(timestamp,tz=pytz.timezone('UTC')),
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
    except:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK,{}

def to_markdown(steam_text):
    """
    steamで書かれた文章をdiscordで使えるように変更
    （[noparse]、[table]は無視されます、[list]と[olist]は同じとみなします）

    Parameters
    ----------
    steam_text : str
        steamのコメント書式に従ったテキスト

    Returns
    ----------
    (return) : str
        discordの書式に従ったテキスト
    """
    # 改行など削って一行に
    oneline_text = re.sub(r' +',' ',re.sub('\s',' ',steam_text))
    # 対応しているタグを置き換え
    fixed_text = re.sub(r'\[/?(((Q|q)uote)|(code))\]','`',re.sub(r'\[/?((h1)|(b))\]','**',re.sub(r'\[/?spoiler\]','||',re.sub(r'\[/?strike\]','~~',re.sub(r'\[/?i\]','*',re.sub(r'\[\*\]',' -',oneline_text.replace('**','＊＊').replace('||','｜｜').replace('~~','～～').replace('`','‘')))))))
    # [quote=xxx]のタグを置き換え
    fixed_text = re.sub(r'\[quote=([^\]]+)\]','`',fixed_text)
    tmp_list = fixed_text.split('[/url]')[0:-1]
    for i in range(len(tmp_list)):
        #[url=example.com]hoge[/url] を　 example.com に
        url = tmp_list[i].split("[url=",1)[1].split("]",1)[0]
        fixed_text = fixed_text.replace('[url='+url+']'+tmp_list[i].split("[url=",1)[1].split("]",1)[1]+'[/url]',' {} '.format(url))
    #対応していないタグを削除し、余分な空白を削除して返却
    return re.sub(r' +',' ',re.sub(r'\[/?((list)|(noparse)|(olist)|(img)|(table)|(tr)|(th)|(td))\]',' ',fixed_text))


def get_last_update(posted_time):
    """
    何日前かカウントする

    Parameters
    ----------
    posted_time : int
        投稿された時間のタイムスタンプ

    Returns
    ----------
    updated_time_status : str
        何日前か表すdiscord形式のテキスト
    """
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

def byte_unit(file_size):
    """
    バイトの単位を変換

    Parameters
    ----------
    file_size : int
        ファイルのバイト数

    Returns
    ----------
    (return) : str
        適切な単位に変換後の文字列
    """
    if file_size < 1024:
        return str(file_size) + ' B'
    elif file_size < 1024**2:
        return str(round(file_size / 1024 ,2)) + ' KB'
    elif file_size < 1024**3:
        return str(round(file_size / 1024**2 ,2)) + ' MB'
    elif file_size < 1024**4:
        return str(round(file_size / 1024**3 ,2)) + ' GB'
    else:
        return str(file_size) + ' B'

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

def main(dc_token,steam_key):
    """
    メインの関数

    Parameters
    ----------
    dc_token : str
        discordのBotのトークン
    steam_key : str
        steam API 接続用のKey
    """
    global setting
    client = discord.Client()

    @client.event
    async def on_ready():
        """
        Bot起動時に動作（通知機能）
        """
        pass

    @client.event
    async def on_message(message):
        global setting
        """
        メッセージが送られた時動作

        Parameters
        ----------
        message : str
            送られたメッセージ
        """

        # チャンネルがtext以外の場合（ボイスチャンネル、DM等）return
        if str(message.channel.type) != 'text':
            return

        # 設定ファイル内にサーバーIDがない場合追加
        if str(message.guild.id) not in setting:
            setting[str(message.guild.id)] = {}
            res = write_setting(setting)
            if res != STANDARD_RETURN.OK:
                print('[warn] first setting failed '+str(message.guild.id))
                return

        # 会話系
        if str(client.user.id) in message.content:
            if random.randint(1,100) > 98:
                await message.channel.send(f'{message.author.mention} ...')
                return
            talk_status = talk(message.content)

            # 非同期によって変数が反映されない？のが心配なので先にリストを作っておく
            talk_list_dt = ['二度とわたしに話しかけないで', '変態ね', 'セクハラよ', 'こんなことしてないで街づくりでもしたらどう？']
            talk_list_tsun = ['知ってる', '当然よね', '当たり前のこと言わないで', 'もっと言ってもいいのよ']
            talk_list_other = ['ん？', 'わからないわ']
            talk_list_ikigomi = ['あんたには負けないんだから', '気合十分よ', '今年も負けないからね']

            if talk_status == TALK_RETURN.DT:
                if message.author.id == org_master:
                    await message.channel.send(f'{message.author.mention} 私を作ってくれたことは感謝してる。でも{random.choice(talk_list_dt)}')
                else:
                    await message.channel.send(f'{message.author.mention} {random.choice(talk_list_dt)}')
            elif talk_status == TALK_RETURN.TSUN:
                await message.channel.send(f'{message.author.mention} {random.choice(talk_list_tsun)}')
            elif talk_status == TALK_RETURN.OTHER:
                await message.channel.send(f'{message.author.mention} {random.choice(talk_list_other)}')
            elif talk_status == TALK_RETURN.IKIGOMI:
                await message.channel.send(f'{message.author.mention}  {random.choice(talk_list_ikigomi)}')
            return

        # 各種設定
        elif message.content.startswith('r/set-gameid'):
            if message.author.id != server_admin and message.author.id != message.guild.owner_id:
                return
            try:
                setting[str(message.guild.id)]['gameid'] = str(int(message.content.split(' ')[1]))
                write_setting(setting)
                await message.channel.send('[OK] gameid = '+str(message.content.split(' ')[1]))
                return
            except:
                traceback.print_exc()
                await message.channel.send('[FAIL] gameid = ???')
                return

        # ヘルプを表示
        elif message.content == ('r/help'):
            embed = discord.Embed()
            embed.add_field(name='s/ word',value='search on steam/steamを検索します', inline=False)
            embed.add_field(name='r/help',value='ヘルプを表示します', inline=False)
            # 管理者だった場合以下も表示
            if message.author.id == server_admin or message.author.id == message.guild.owner_id:
                embed.add_field(name='r/set-gameid',value='You can get gameid on url of storepage. e.g.(Cities:Skylines) r/set-gameid 255710', inline=False)
            embed.set_footer(text='Reika ver '+str(__version__))
            await message.channel.send(embed=embed)
            return

        # 検索機能
        elif message.content.startswith('s/'):
            raw_searchtext = message.content.split(' ')
            if len(raw_searchtext) == 1:
                return
            search_word = []
            for i in range(1,len(raw_searchtext)):
                search_word.append(raw_searchtext[i])
            try:
                app_id = setting[str(message.guild.id)]['gameid']
            except:
                await message.channel.send('`r/set-gameid`コマンドを使用してゲームIDをセットしてください。')
                return
            ret,res = searchitem(search_word,steam_key,app_id)
            if ret != STANDARD_RETURN.OK:
                await message.channel.send('何も見つからなかった...')
                return
            embed = discord.Embed(title=res['title'],url=res['url'],description=res['description'], timestamp=res['timestamp'])
            embed.set_author(url=res['author']['url'], name=res['author']['name'],icon_url=res['author']['icon_url'])
            embed.set_thumbnail(url=res['thumbnail'])
            for i in range(1,len(res['field'])+1):
                embed.add_field(name=res['field']['field'+str(i)]['name'],value=res['field']['field'+str(i)]['value'], inline=res['field']['field'+str(i)]['inline'])
            embed.set_footer(text=res['footer'])
            await message.channel.send(embed=embed)
            return

        message_text = message.content
        for i in message.raw_mentions:
            message_text = message_text.replace('<@'+str(i)+'>','<@'+str(i)+'> ')
        message_text = message_text.replace('\n',' ').replace('　',' ').split(' ')
        for i in message_text:
            url = re.fullmatch(r'https://steamcommunity.com/((sharedfiles)|(workshop))/filedetails/\?id=[0-9]+.*',i)
            if url:
                ret,res = get_contentdetail(str(int(urllib.parse.parse_qs(urllib.parse.urlparse(url.group()).query)['id'][0])),steam_key)
                if ret != STANDARD_RETURN.OK:
                    raise Exception
                embed = discord.Embed(title=res['title'],url=res['url'],description=res['description'], timestamp=res['timestamp'])
                embed.set_author(url=res['author']['url'], name=res['author']['name'],icon_url=res['author']['icon_url'])
                embed.set_thumbnail(url=res['thumbnail'])
                for i in range(1,len(res['field'])+1):
                    embed.add_field(name=res['field']['field'+str(i)]['name'],value=res['field']['field'+str(i)]['value'], inline=res['field']['field'+str(i)]['inline'])
                embed.set_footer(text=res['footer'])
                await message.channel.send(embed=embed)

    client.run(dc_token)

if __name__ == '__main__':
    ret,res = read_setting()
    if ret == STANDARD_RETURN.OK:
        setting = res
    else:
        ret = write_setting(setting)
        if ret != STANDARD_RETURN.OK:
            raise Exception
    main(sys.argv[1],sys.argv[2])
