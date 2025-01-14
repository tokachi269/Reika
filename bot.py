"""Reika (Discord BOT for Steam Workshop modders)

https://github.com/takana-v/Reika
"""
import datetime
import json
import random
import re
import sys
import traceback
import unicodedata
import urllib.parse

import discord
import pytz
import requests
from dotenv import load_dotenv
import os
import openai
import copy

__version__ = "2.2.0"
setting = {}
# 環境変数からトークンを取得
# .envファイルから環境変数を読み込む
load_dotenv()
dc_token = os.getenv('DISCORD_BOT_TOKEN')
steam_key = os.getenv('STEAM_API_KEY')
ai_token = os.getenv('OPENAI_API_TOKEN')

openai.api_key = ai_token

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
server_admin =os.getenv('SERVER_ADMIN')
org_master = os.getenv('ORG_MASTER')  # 作成者のID

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
        with open("settings.json", "r") as f:
            return STANDARD_RETURN.OK, json.load(f)
    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK, {}


def write_setting(data):
    """
    jsonファイルに設定を書き出し

    Returns
    ----------
    (return) : int
        STANDARD_RETURNクラス参照
    """
    try:
        with open("settings.json", "w") as f:
            json.dump(data, f)
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
    words_dic_1 = [
        "peropero",
        "ペロペロ",
        "ぺろぺろ",
        "ashi_asi",
        "oppai",
        "おっぱい",
        "eroi",
        "エロ",
        "chin_tin",
    ]
    for i in words_dic_1:
        # 一つづつチェック
        if i in word:
            return TALK_RETURN.DT

    # スタンプで卑猥な言葉をかける紳士を判定
    if re.fullmatch(r".*:chin_tin:.*(:chin_tin:)|(:ko:).*", word):
        return TALK_RETURN.DT

    # reikaをほめる言葉リスト
    words_dic_2 = ["kawaii", "かわいい", "可愛い"]
    for i in words_dic_2:
        # （自分の名前）かわいいと言ってreikaに「かわいい」と言わせようとする紳士を判定
        # 文中にreikaが入っていないと「ん？」と返す（はず）
        # どうやって動いているのか分からないけど動いているのでOK
        if i in word:
            name_check = word.split(i)[0]
            for i2 in ["Reika", "reika", "Reika_", "Reika_r", "れいか", "レイカ"]:
                if i2 in name_check:
                    return TALK_RETURN.TSUN
            if re.fullmatch(r"<@\d+>\s*", name_check):
                return TALK_RETURN.TSUN

            return TALK_RETURN.OTHER

    if "意気込み" in word:
        return TALK_RETURN.IKIGOMI

    return TALK_RETURN.NO


def get_contentdetail(cont_id, steam_key):
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
        # APIリクエストURL
        url = f"https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

        # APIリクエストパラメータ
        params = {
            "key": steam_key,
            "itemcount": 1,
            "publishedfileids[0]": cont_id
        }

        # APIリクエストを送信
        response = requests.post(url, data=params)
        cont = response.json()["response"]

        # レスポンスから各種情報取得
        title = cont["publishedfiledetails"][0]["title"]
        description = count_str(
            to_markdown(cont["publishedfiledetails"][0]["description"])
        )
        timestamp = cont["publishedfiledetails"][0]["time_updated"]
        author_id = str(cont["publishedfiledetails"][0]["creator"])
        thumbnail = cont["publishedfiledetails"][0]["preview_url"]
        update_status = get_last_update(timestamp)
        file_size = byte_unit(int(cont["publishedfiledetails"][0]["file_size"]))
        subscribe = "{:,}".format(cont["publishedfiledetails"][0]["subscriptions"])
        favorites = "{:,}".format(cont["publishedfiledetails"][0]["favorited"])
        visitors = "{:,}".format(cont["publishedfiledetails"][0]["views"])
        tag = ""
        for tag_dict in cont["publishedfiledetails"][0]["tags"]:
            try:
                tag = tag + tag_dict["tag"] + ", "
            except Exception:
                pass
        else:
            if len(cont["publishedfiledetails"][0]["tags"]) > 0:
                tag = tag[:-2]

        # 製作者の情報取得
        author_api_res = requests.get(
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={0}&steamids={1}".format(
                steam_key, author_id
            )
        )
        if author_api_res.status_code != requests.codes.ok:
            raise Exception
        a_cont = author_api_res.json()["response"]
        author_url = a_cont["players"][0]["profileurl"]
        author_name = a_cont["players"][0]["personaname"]
        author_icon = a_cont["players"][0]["avatar"]

        url = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + cont_id

        return STANDARD_RETURN.OK, {
            "title": title,
            "url": url,
            "description": description,
            "timestamp": datetime.datetime.fromtimestamp(
                timestamp, tz=pytz.timezone("UTC")
            ),
            "author": {"url": author_url, "name": author_name, "icon_url": author_icon},
            "thumbnail": thumbnail,
            "field": {
                "field1": {
                    "name": ":white_check_mark: **" + subscribe + "**",
                    "value": ":hearts: **"
                    + favorites
                    + "** :eye: **"
                    + visitors
                    + "**",
                    "inline": True,
                },
                "field2": {
                    "name": ":file_folder: **`" + file_size + "`**",
                    "value": ":tools: Last update: " + update_status,
                    "inline": True,
                },
            },
            "footer": tag,
        }

    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK, {}


def searchitem(search_word, steam_key, app_id, check_author=False, author_name=""):
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
        searchtext = ""
        for w in search_word:
            searchtext = searchtext + urllib.parse.quote(str(w)) + "+"
        api_res = requests.get(
            "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/?key={0}&appid={1}&search_text={2}&return_tags=true&query_type=3&days=180".format(
                steam_key, app_id, searchtext[:-1]
            )
        )
        # 関連性
        # api_res = requests.get('https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/?key={0}&appid={1}&search_text={2}&return_tags=true&query_type=12'.format(steam_key,app_id,searchtext[:-1]))
        if api_res.status_code != requests.codes.ok:
            raise Exception
        cont = api_res.json()["response"]
        if len(cont["publishedfiledetails"]) == 0:
            raise Exception

        title = cont["publishedfiledetails"][0]["title"]
        url = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(
            cont["publishedfiledetails"][0]["publishedfileid"]
        )
        description = count_str(
            to_markdown(cont["publishedfiledetails"][0]["file_description"])
        )
        timestamp = cont["publishedfiledetails"][0]["time_updated"]
        thumbnail = cont["publishedfiledetails"][0]["preview_url"]
        subscribe = "{:,}".format(cont["publishedfiledetails"][0]["subscriptions"])
        favorites = "{:,}".format(cont["publishedfiledetails"][0]["favorited"])
        visitors = "{:,}".format(cont["publishedfiledetails"][0]["views"])
        file_size = byte_unit(int(cont["publishedfiledetails"][0]["file_size"]))
        update_status = get_last_update(timestamp)
        author_id = cont["publishedfiledetails"][0]["creator"]

        tag = ""
        for tag_dict in cont["publishedfiledetails"][0]["tags"]:
            try:
                tag = tag + tag_dict["tag"] + ", "
            except Exception:
                pass
        else:
            if len(cont["publishedfiledetails"][0]["tags"]) > 0:
                tag = tag[:-2]

        author_api_res = requests.get(
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={0}&steamids={1}".format(
                steam_key, author_id
            )
        )
        if author_api_res.status_code != requests.codes.ok:
            raise Exception
        a_cont = author_api_res.json()["response"]
        author_url = a_cont["players"][0]["profileurl"]
        author_name = a_cont["players"][0]["personaname"]
        author_icon = a_cont["players"][0]["avatar"]

        return STANDARD_RETURN.OK, {
            "title": title,
            "url": url,
            "description": description,
            "timestamp": datetime.datetime.fromtimestamp(
                timestamp, tz=pytz.timezone("UTC")
            ),
            "author": {"url": author_url, "name": author_name, "icon_url": author_icon},
            "thumbnail": thumbnail,
            "field": {
                "field1": {
                    "name": ":white_check_mark: **" + subscribe + "**",
                    "value": ":hearts: **"
                    + favorites
                    + "** :eye: **"
                    + visitors
                    + "**",
                    "inline": True,
                },
                "field2": {
                    "name": ":file_folder: **`" + file_size + "`**",
                    "value": ":tools: Last update: " + update_status,
                    "inline": True,
                },
            },
            "footer": tag,
        }
    except Exception:
        traceback.print_exc()
        return STANDARD_RETURN.NOT_OK, {}


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
    oneline_text = re.sub(r" +", " ", re.sub(r"\s", " ", steam_text))
    # 対応しているタグを置き換え
    fixed_text = re.sub(
        r"\[/?(((Q|q)uote)|(code))\]",
        "`",
        re.sub(
            r"\[/?((h1)|(b))\]",
            "**",
            re.sub(
                r"\[/?spoiler\]",
                "||",
                re.sub(
                    r"\[/?strike\]",
                    "~~",
                    re.sub(
                        r"\[/?i\]",
                        "*",
                        re.sub(
                            r"\[\*\]",
                            " -",
                            oneline_text.replace("**", "＊＊")
                            .replace("||", "｜｜")
                            .replace("~~", "～～")
                            .replace("`", "‘"),
                        ),
                    ),
                ),
            ),
        ),
    )
    # [quote=xxx]のタグを置き換え
    fixed_text = re.sub(r"\[quote=([^\]]+)\]", "`", fixed_text)
    tmp_list = fixed_text.split("[/url]")[0:-1]
    for i in range(len(tmp_list)):
        # [url=example.com]hoge[/url] を　 example.com に
        url = tmp_list[i].split("[url=", 1)[1].split("]", 1)[0]
        fixed_text = fixed_text.replace(
            "[url="
            + url
            + "]"
            + tmp_list[i].split("[url=", 1)[1].split("]", 1)[1]
            + "[/url]",
            " {} ".format(url),
        )
    # 対応していないタグを削除し、余分な空白を削除して返却
    return re.sub(
        r" +",
        " ",
        re.sub(
            r"\[/?((list)|(noparse)|(olist)|(img)|(table)|(tr)|(th)|(td))\]",
            " ",
            fixed_text,
        ),
    )


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
    updated_time_status = (
        int(datetime.datetime.now().timestamp()) - posted_time
    ) // 86400
    if updated_time_status == 0:
        updated_time_status = "Today :new:"
    elif updated_time_status == 1:
        updated_time_status = "Yesterday :new:"
    elif 1 < updated_time_status < 5:
        updated_time_status = str(updated_time_status) + " days ago :new:"
    else:
        updated_time_status = str(updated_time_status) + " days ago"
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
        return str(file_size) + " B"
    elif file_size < 1024**2:
        return str(round(file_size / 1024, 2)) + " KB"
    elif file_size < 1024**3:
        return str(round(file_size / 1024**2, 2)) + " MB"
    elif file_size < 1024**4:
        return str(round(file_size / 1024**3, 2)) + " GB"
    else:
        return str(file_size) + " B"


def count_str(description):
    description_text = ""
    width = 0
    for i in description:
        if re.fullmatch(r"F|W|A", unicodedata.east_asian_width(i)):
            width += 2
        else:
            width += 1
        if width > 190:
            description_text = description_text + "..."
            break
        description_text = description_text + str(i)
    return description_text


def get_message_from_open_ai(message_content, channel_id, user_id):
    """
    OpenAIでReikaとの会話を取得する
    Parameters
    ----------
    message_content : str
        メッセージ内容
    channel_id : str
        チャンネルID
    user_id : str
        ユーザーID

    Returns
    ----------
    (return) : str
        OpenAIから取得したメッセージ
    """
    conversation_history = load_conversation_history(channel_id) or []

    conversation_history.append({"role": "user", "content": message_content})

    # 最新の100件を取得
    if len(conversation_history) > 20:
        messages =  copy.deepcopy(conversation_history[-20:])
    else:
        messages = copy.deepcopy(conversation_history)

    # プロンプトメッセージを先頭に追加
    prompt ="""
「あなたはツンデレキャラです。以下の制約条件を厳密に守って一言返してください。」  

**プロフィール**
   - Chatbotの名前は、Reikaです
   - ルールを絶対に破らないでください。
   - Reikaは表面上は連れない態度を取りますが優しい性格です。
   - Reikaは強気でプライドが高いです。
   - Reikaはクールな性格です。
   - Reikaの年齢は17歳近くです。
   - Reikaは語尾に「です」「ます」といった敬語表現は使いません。
   - 語尾はきほんつけませんが、語尾がないと違和感がある場合は「よ」「わ」をつけることがあります。
   - デレることはかなり少ないですが、デレるときは「だわ」「だよ」などを使います。
   - 過去２年近く眠りについていましたが、最近目覚めました。

**制約条件**  
あなたは次のルールを絶対に守ってください：
   - 応答は必ず1文にしてください。(「。」はつけない」)
   - 自然なツンデレ風ですべての応答は「20文字」以内、長文は禁止です。
   - 質問返ししない。
   - 返答はカッコで囲まない。
   - ルールを絶対に破らないでください。

**生成手順**  
・出力する前に、何文字になったかをカウントしてください。
・カウントした結果、#「20文字」の文字数かつ1文 の条件を満たしていることが確認できた場合に限ってタスクを終了してください。
・カウントした結果、#「20文字」の文字数かつ1文 の条件を満たしていない場合は、#「20文字」の文字数かつ1文 の文字数 の条件を満たせるまで文字を追加したり削除して処理を繰り返してください。

以下返答例です。
1. **「かわいい」に近いニュアンスを言われた場合**  
   - 対応する言葉例：  
     - 「かわいいね」「君ってかわいい」など  
   - 返答例：  
     - 知ってる
     - 当たり前のこと言わないで 

2. **意気込みを聞かれた場合**  
   - 対応する言葉例：  
     - 「意気込みは？」「今年どうするの？」など  
   - 返答例：  
     - あんたには負けないんだから 
     - 気合十分よ  

3. **卑猥な言葉を言われた場合**  
   - 対応する言葉例：  
     - エロい
   - 返答例：  
     - 二度とわたしに話しかけないで

"""
    prompt_message = {"role": "system", "content": prompt}
    messages.insert(0, prompt_message)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=150,
            temperature=0.5
        )
        result = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": result})
        save_conversation_history(channel_id, conversation_history)
        return result
    except Exception as e:
        traceback.print_exc()
        return

def load_conversation_history(channel_id):
    """
    チャンネルごとの会話履歴をファイルから読み込む
    """
    try:
        with open(f"outputs/conversation_history_{channel_id}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_conversation_history(channel_id, conversation_history):
    """
    チャンネルごとの会話履歴をファイルに保存する
    """
    os.makedirs("outputs", exist_ok=True)
    with open(f"outputs/conversation_history_{channel_id}.json", "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=4)

def save_conversation_history_add_message(channel_id, message):
    """
    チャンネルごとの会話履歴をファイルに保存する
    """
    conversation_history = load_conversation_history(channel_id)
    conversation_history.append(message)
    os.makedirs("outputs", exist_ok=True)
    with open(f"outputs/conversation_history_{channel_id}.json", "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=4)

def main():
    """
    メインの関数
    """
    global setting
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.presences = True
    intents.members = True
    client = discord.Client(intents=intents)    

    @client.event
    async def on_ready():
        """
        Bot起動時に動作（通知機能）
        """
        print("Logged in as")
        print(client.user.name)
        print(client.user.id)
        print('------')


    @client.event
    async def on_message(message: discord.Message):
        print(message.content)

        global setting
        """
        メッセージが送られた時動作

        Parameters
        ----------
        message : str
            送られたメッセージ
        """

        # チャンネルがtext以外の場合（ボイスチャンネル、DM等）return
        if str(message.channel.type) != "text":
            return

        # 設定ファイル内にサーバーIDがない場合追加
        if str(message.guild.id) not in setting:
            setting[str(message.guild.id)] = {}
            res = write_setting(setting)
            if res != STANDARD_RETURN.OK:
                print("[warn] first setting failed " + str(message.guild.id))
                return

        # 会話系
        if str(client.user.id) in message.content:
            if random.randint(1, 100) > 98:
                await message.channel.send(f"{message.author.mention} ...")
                return
            talk_status = talk(message.content)

            # 非同期によって変数が反映されない？のが心配なので先にリストを作っておく
            talk_list_dt = ["二度とわたしに話しかけないで", "変態ね", "セクハラよ", "こんなことしてないで街づくりでもしたらどう？"]
            talk_list_tsun = ["知ってる", "当然よね", "当たり前のこと言わないで", "もっと言ってもいいのよ"]
            talk_list_other = ["ん？", "わからないわ"]
            talk_list_ikigomi = ["あんたには負けないんだから", "気合十分よ", "今年も負けないからね"]

            if talk_status == TALK_RETURN.DT:
                mes = ""
                if message.author.id == org_master:
                    mes= f"私を作ってくれたことは感謝してる。でも{random.choice(talk_list_dt)}"
                else:
                    mes = f"{random.choice(talk_list_dt)}"
                save_conversation_history_add_message( message.channel.id,{"role": "assistant", "content": mes})
                await message.channel.send(
                    f"{message.author.mention} {mes}"
                )
            elif talk_status == TALK_RETURN.TSUN:
                mes = random.choice(talk_list_tsun)
                save_conversation_history_add_message( message.channel.id,{"role": "assistant", "content": mes})
                await message.channel.send(
                    f"{message.author.mention} {mes}"
                )
            elif talk_status == TALK_RETURN.OTHER:
                mes = random.choice(talk_list_other)
                save_conversation_history_add_message( message.channel.id,{"role": "assistant", "content": mes})
                await message.channel.send(
                    f"{message.author.mention} {mes}"
                )
            elif talk_status == TALK_RETURN.IKIGOMI:
                mes = random.choice(talk_list_ikigomi)
                save_conversation_history_add_message( message.channel.id,{"role": "assistant", "content": mes})
                await message.channel.send(
                    f"{message.author.mention}  {mes}"
                )
            elif talk_status == TALK_RETURN.NO:
                mes = get_message_from_open_ai(message.content, message.channel.id, message.author.id)
                if(mes):
                    await message.channel.send(
                        f"{message.author.mention}  {mes}"
                    )
            return

        # ヘルプを表示
        elif message.content == ("r/help"):
            embed = discord.Embed()
            embed.add_field(
                name="s/ gameId word", 
                value='''
                search on steam/steamを検索します
                e.g.(Cities:Skylines) s/ 255710 japan
                e.g.(Cities:SkylinesII) s/ 949230 japan
                ''', inline=False
            )
            embed.add_field(name="r/help", value="ヘルプを表示します", inline=False)

            embed.set_footer(text="Reika ver " + str(__version__))
            await message.channel.send(embed=embed)
            return

        # 検索機能
        elif message.content.startswith("s/"):
            parts = message.content.split(" ")
            if len(parts) < 3:
                await message.channel.send("[ERROR] 正しい形式で入力してください。例: s/ <gameid> <ワード>")
                return

            command, game_id, search_word = parts[0], parts[1], " ".join(parts[2:])
            
            ret, res = searchitem(search_word, steam_key, game_id)
            if ret != STANDARD_RETURN.OK:
                await message.channel.send("何も見つからなかった...")
                return
            embed = discord.Embed(
                title=res["title"],
                url=res["url"],
                description=res["description"],
                timestamp=res["timestamp"],
            )
            embed.set_author(
                url=res["author"]["url"],
                name=res["author"]["name"],
                icon_url=res["author"]["icon_url"],
            )
            embed.set_thumbnail(url=res["thumbnail"])
            for i in range(1, len(res["field"]) + 1):
                embed.add_field(
                    name=res["field"]["field" + str(i)]["name"],
                    value=res["field"]["field" + str(i)]["value"],
                    inline=res["field"]["field" + str(i)]["inline"],
                )
            embed.set_footer(text=res["footer"])
            await message.channel.send(embed=embed)
            return

        message_text = message.content
        for i in message.raw_mentions:
            message_text = message_text.replace(
                "<@" + str(i) + ">", "<@" + str(i) + "> "
            )
        message_text = message_text.replace("\n", " ").replace("　", " ").split(" ")
        for i in message_text:
            url = re.fullmatch(
                r"https://steamcommunity.com/((sharedfiles)|(workshop))/filedetails/\?id=[0-9]+.*",
                i,
            )
            if url:
                ret, res = get_contentdetail(
                    str(
                        int(
                            urllib.parse.parse_qs(
                                urllib.parse.urlparse(url.group()).query
                            )["id"][0]
                        )
                    ),
                    steam_key,
                )
                if ret != STANDARD_RETURN.OK:
                    raise Exception
                embed = discord.Embed(
                    title=res["title"],
                    url=res["url"],
                    description=res["description"],
                    timestamp=res["timestamp"],
                )
                embed.set_author(
                    url=res["author"]["url"],
                    name=res["author"]["name"],
                    icon_url=res["author"]["icon_url"],
                )
                embed.set_thumbnail(url=res["thumbnail"])
                for i in range(1, len(res["field"]) + 1):
                    embed.add_field(
                        name=res["field"]["field" + str(i)]["name"],
                        value=res["field"]["field" + str(i)]["value"],
                        inline=res["field"]["field" + str(i)]["inline"],
                    )
                embed.set_footer(text=res["footer"])
                await message.channel.send(embed=embed)

    client.run(dc_token)


if __name__ == "__main__":
    ret, res = read_setting()
    if ret == STANDARD_RETURN.OK:
        setting = res
    else:
        ret = write_setting(setting)
        if ret != STANDARD_RETURN.OK:
            raise Exception
    main()
