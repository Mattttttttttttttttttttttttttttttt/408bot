"""this module runs 408 bot"""

# no todos yet

import os
from time import sleep
from datetime import timezone, timedelta
import datetime
import re
import shelve
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv
import discord
from helpers import find_all, valid_num


load_dotenv()

# gives the bot message content intent
intents = discord.Intents.default()
intents.message_content, intents.reactions = True, True

# creates bot
TOKEN = os.getenv("TOKEN")
bot = commands.Bot(command_prefix="!", intents=intents)


# time stamps and channel/server ids
PDT = timezone(timedelta(hours=-7))
PST = timezone(timedelta(hours=-8))
CST = timezone(timedelta(hours=-6))
PDT_408 = datetime.time(16, 7, 0, tzinfo=PDT)
PDT_409 = datetime.time(16, 9, 0, tzinfo=PDT)
PST_408 = datetime.time(16, 7, 0, tzinfo=PST)
PST_409 = datetime.time(16, 9, 0, tzinfo=PST)
CST_408 = datetime.time(16, 7, 0, tzinfo=CST)
CST_409 = datetime.time(16, 9, 0, tzinfo=CST)
PDT_625 = datetime.time(18, 24, 0, tzinfo=PDT)
PDT_626 = datetime.time(18, 26, 0, tzinfo=PDT)
CHANNEL_408_ID = 1231756043810508822
CHANNEL_408: discord.TextChannel
CHANNEL_SUGGESTIONS = 1294100441721737287
TEST_SERVER_ID = 1240098098513055776
WCB_ID = 1204222579498557440
DEVELOPER = 1104220935973777459
LIST_408 = [16, 8]
LIST_HRISHU = [15, 8]
LIST_625 = [18, 25]

# variables
medal: int
users: list = [] #[message.author.id, ms]
need_to_react: list = []
records_408: list = [] #one element = [user id, ms, lb id]
records_625: list = []
last_vc_ping: datetime.datetime = datetime.datetime(2000, 1, 1, tzinfo=timezone.utc)
UTC_TO_PDT: int = -7
UTC_TO_PST: int = -8
EMOJI_408 = "<:408:1232116288113999953>"
ROLE_408 = "<@&1233927005477797901>"
EMOJI_625 = "<:625:1246228026006442077>"
ROLE_625 = "<@&1246226716100268124>"
VC_PING = "<@&1204276473150578698>"
RANKING_TO_EMOJI = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟"
    }
EMOJI_TO_TEXT = {EMOJI_408: "408",
                 EMOJI_625: "625"}


# VIEW CLASS
class Buttons(discord.ui.View):
    """class representing a group of back and forward buttons"""

    records: list
    page: int
    max_page: int

    def __init__(self, records: list) -> None:
        super().__init__(timeout=120)
        self.records = records
        self.page = 0
        self.max_page = len(records) - 1

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.gray, disabled=True,
                       custom_id="back")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        """turn page back

        Args:
            inter (discord.Interaction): default parameter
        """
        if self.page == 0:
            return None
        elif self.page == 1:
            button.disabled = True
        self.page -= 1
        if self.page != self.max_page:
            [i for i in self.children if i.custom_id == "forward"][0].disabled = False
        await inter.response.edit_message(embed=self.records[self.page], view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.gray, custom_id="forward")
    async def forward(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        """turn page forward

        Args:
            inter (discord.Interaction): default parameter
        """
        if self.page == self.max_page:
            return None
        elif self.page == self.max_page - 1:
            button.disabled = True
        self.page += 1
        if self.page != 0:
            [i for i in self.children if i.custom_id == "back"][0].disabled = False
        await inter.response.edit_message(embed=self.records[self.page], view=self)


# HELPER FUNCTIONS
def s_ms(t: int) -> str:
    """returns a string describing the time length given a microsecond

    Args:
        time (int): time in millisecond

    Returns:
        str: string describing the time length
    """
    return str(t/1000) + "s" if t >= 1000 else str(t) + "ms"
    # either ~ 1s or 500ms


def pdt_h(hour: str) -> str:
    """returns a UTC hour in PDT, both 2-digit numbers

    Args:
        hour (str): hour in UTC

    Returns:
        str: hour in PDT
    """
    if int(hour) > -1 * UTC_TO_PDT:
        return str(valid_num(int(hour) + UTC_TO_PDT))
    else:
        return str(valid_num(int(hour) + UTC_TO_PDT + 24))
    # it's valid_num-ed


def pdt_hm(t: str) -> str:
    """returns a UTC time in PDT, both 2-digit numbers

    Args:
        t (str): UTC time formatted in %m:%s

    Returns:
        str: PDT time formatted in %m:%s
    """
    return pdt_h(t.split(":")[0]) + ":" + valid_num(int(t.split(":")[1]))


def list_time(lst: list) -> str:
    """returns a formatted correctly timestamp from a list

    Args:
        lst (list): list of [%m, %s]

    Returns:
        str: correctly formatted string of timestamp
    """
    return valid_num(lst[0]) + ":" + valid_num(lst[1])


def second_value(val: list) -> int:
    """returns the second value of a list
    used for sort() function

    Args:
        val (list): the list passed as sort() is called

    Returns:
        int: the second value of that list
    """
    return val[1]


def filter_records(record: list[list], first_item: int) -> list:
    """keeps the element of the input list that has the given first item

    Args:
        record (list[list]): the input list
        first_item (int): the first item of the sublist of the input list

    Returns:
        list: the filtered list
    """
    result = []
    for i in record:
        if i[0] == first_item:
            result.append(i)
    return result


async def send_long_message(inter: discord.Interaction, content: list,
                            user: int | None=None)-> None:
    """sends a long message in chunk of 2000 characters

    Args:
        inter (discord.Interaction): the interaction to respond to
        content (list): the content to send
        user (int | None): if the message is private, the user to send the following messages to
    """
    while len(content[-1]) > 2000:
        content.append(content[-1][0:2000])
        content.append(content[-2][2000:])
        del content[-3]
    if user:
        user = await bot.fetch_user(user)
        await user.send(content[0])
    else:
        await inter.edit_original_response(content=content[0])
    if len(content) > 1:
        for i, txt in enumerate(content):
            if i == 0:
                continue
            if user:
                await user.send(content=txt)
            else:
                await inter.channel.send(content=txt)


async def react(message: discord.Message, timestamp: list, t: list|None = None):
    """react to the given message with different emojis

    Args:
        message (discord.Message): the message to react to
        timestamp (list): the time the message was sent at, ["04:08", t (in ms)]
        t (list, optional): the target time for the message. Defaults to None.
    """
    global medal, need_to_react
    if t is None:
        print(f"target time: idfk bruh, sent time: {timestamp[0]}")
        await message.add_reaction("💀")
    else:
        plus = list_time([t[0], t[1]+1])
        minus = list_time([t[0], t[1]-1])
        t = list_time(t)
        user_ids = [users[i][0] for i in range(len(users))]
        if timestamp[0] == t and message.author.id not in user_ids and medal < 10:
            users.append([message.author.id, timestamp[1]])
            # ^this is first because in the condition above there's "in user_ids"
            need_to_react.append([message, timestamp[1]])
            sleep(max(bot.latency, 0.5))
            copy = medal = medal + 1
            need_to_react.sort(key=second_value)
            await need_to_react.pop(0)[0].add_reaction(RANKING_TO_EMOJI[copy])
            print(f"reacted with {RANKING_TO_EMOJI[copy]}")
            # adds the user id to a list, along with the ms
        elif timestamp[0] == t and (message.author.id in user_ids or medal >= 10):
            await message.add_reaction("🙂")
        elif timestamp[0] == plus or timestamp[0] == minus:
            await message.add_reaction("☠️")
        else:
            print(f"target time: {t}, sent time: {timestamp[0]}")
            await message.add_reaction("💀")


async def send_leaderboard(timestamp: str, hrishu: bool) -> None:
    """sends a specific leaderboard to #408

    Args:
        timestamp (str): a timestamp indicating which leaderboard to send (308, 408, 625)
        hrishu (bool): whether it's 308, which doesn't not have data leaderboard
    """
    # users = [[user id, time in ms], ...]
    global users
    if not users:
        await CHANNEL_408.send(
            f'''# {datetime.datetime.now(PDT).strftime("%m/%d/%Y")} leaderboard
bruh not a single person did {timestamp} today''')
        print("sent empty leaderboard " + timestamp)
    else:
        users.sort(key=second_value)
        message = f"# {datetime.datetime.now(PDT).strftime("%m/%d/%Y")} {timestamp} leaderboard"
        for i, [user, t] in enumerate(users, 1): #user id and ms
            message += f"\n{RANKING_TO_EMOJI[i]} <@{user}> {s_ms(t)}"
        msg = await CHANNEL_408.send(message)
        print("sent leaderboard " + timestamp)
        if not hrishu:
            for [user, t] in users:
                await update(user, [t, msg.id], timestamp) #updates record
            await update_file() #updates the file
        users = []


async def update(author: int, speed: list, time: str) -> None:
    """updates the records list

    Args:
        author (int): the id of the person who got the time
        speed (list): a list of the time they achieved in ms, and the message id
        time (str): the time of the day (408 or 625)
    """
    if time == "408":
        global records_408
        temp_records_408 = sorted(filter_records(records_408, author), key=second_value)
        if len(temp_records_408) < 5:
            records_408.append([author, speed[0], speed[1]])
        elif speed[0] <= temp_records_408[-1][1]:
            records_408.append([author, speed[0], speed[1]])
            records_408.remove(temp_records_408[-1])
            # ^no need to sort since it's sorted at get_records
    elif time == "625":
        global records_625
        temp_records_625 = sorted(filter_records(records_625, author), key=second_value)
        if len(temp_records_625) < 5:
            records_625.append([author, speed[0], speed[1]])
        elif speed[0] <= temp_records_625[-1][1]:
            records_625.append([author, speed[0], speed[1]])
            records_625.remove(temp_records_625[-1])


async def update_file() -> None:
    """writes records_408 and records_625 to a file
    """
    file = shelve.open("data")
    file["408"] = records_408
    file["625"] = records_625
    file.close()

async def get_records(user: int | None, t: str | None) -> discord.Embed:
    """returns the records of the server

    Args:
        user (int | None): the id of the user requested, or none
        t (str | None): 408 or 625, or none

    Returns:
        discord.Embed: the embed to return
    """
    assert t is not None, "you can't have an empty time"
    if user is None:
        title = f"{t} Leaderboard:"
        if t == "408":
            record = await get_time_records(records_408)
        elif t == "625":
            record = await get_time_records(records_625)
    else: # user is not None
        title = f"{t} Leaderboard:"
        if t == "408":
            record = f"<@{user}>:\n" +\
                    await get_user_time_records(filter_records(records_408, user))
        elif t == "625":
            record = f"<@{user}>:\n" +\
                    await get_user_time_records(filter_records(records_625, user))
    new_record = [record]
    if find_all(record, "\n") > 9: # has more than 10 entries
        new_record = []
        for i, entry in enumerate(record.split("\n")):
            if i % 10 != 0:
                new_record[-1] = "\n".join([new_record[-1], entry])
            else:
                new_record.append(entry)
    record = new_record
    result: list[discord.Embed] = []
    for i in record:
        result.append(discord.Embed(
            title=title,
            description=i,
            color=discord.Color(65535))) #00ffff
    return result


async def get_user_time_records(records: list) -> str:
    """generates a leaderboard formated string from a user-specific records list
    used when both user and time is given

    Args:
        records (list): a sublist of records_408 or _625 that only has a given user

    Returns:
        str: the leaderboard formated string
    """
    if records == []:
        return "no data yet :)"
    else:
        records.sort(key=second_value)
        record = []
        for i, data in enumerate(records):
            #key = user id, val = time in ms, id = id to leaderboard sent
            msg = await CHANNEL_408.fetch_message(data[2])
            msg = f"https://discord.com/channels/{WCB_ID}/{CHANNEL_408_ID}/{msg.id}"
            record.append(f"{i + 1}. [{s_ms(data[1])}]({msg})")
            #e.g. 1. 0ms: @matt
        return "\n".join(record)


async def get_time_records(records: list) -> str:
    """generates a leaderboard formated string from a records list
    used when time is given but user is not

    Args:
        records (list): the records to look at

    Returns:
        str: the leaderboard formated string
    """
    if records == []:
        return "no data yet :)"
    else:
        records.sort(key=second_value)
        record = []
        for i, [key, val, msg] in enumerate(records):
            #key = user id, val = time in ms, id = id to leaderboard sent
            msg = await CHANNEL_408.fetch_message(msg)
            msg = f"https://discord.com/channels/{WCB_ID}/{CHANNEL_408_ID}/{msg.id}"
            record.append(f"{i + 1}. [{s_ms(val)}]({msg}): <@{key}>")
            #e.g. 1. 0ms: @matt
        return "\n".join(record)


# BOT COMMANDS
@bot.tree.command(name="getdata", description="get the data of this server")
@app_commands.default_permissions()
async def getdata(inter: discord.Interaction) -> None:
    """get the data of the server in a string

    Args:
        inter (discord.Interaction): default parameter
    """
    await inter.response.defer(ephemeral=True)
    content = [f'''*408*
{"\n".join([f"a{id} {t} {msg}" for id, t, msg in records_408])}
*625*
{"\n".join([f"a{id} {t} {msg}" for id, t, msg in records_625])}''']
    await send_long_message(inter, content, inter.user.id)
    await inter.response.edit_message(content="sent to your dm")
    # outputs
    # 408
    # a(user id) (time in ms) (id to leaderboard message)
    # ...
    # 625
    # ...


@bot.tree.command(name="feeddata", description="DANGEROUS: append to the data of this server")
@app_commands.default_permissions()
async def feeddata(inter: discord.Interaction, data: str, overwrite: bool) -> None:
    """feed in the data for the server in a string

    Args:
        inter (discord.Interaction): default parameter
        data (str): the data in the format of "408 a(user id) (ms) (leaderboard message id) 625 ..."
        overwrite (bool): whether to overwrite the original data
    """
    await inter.response.defer(ephemeral=True)
    global records_408, records_625
    if overwrite:
        records_408 = []
        records_625 = []
    data = re.compile(r"\*408\* (.*) \*625\* (.*)").search(data)
    data_408 = re.compile(r"a(\d+) (\d+) (\d+)").findall(data.group(1))
    data_625 = re.compile(r"a(\d+) (\d+) (\d+)").findall(data.group(2))
    for i in data_408:
        await update(int(i[0]), [int(i[1]), int(i[2])], "408")
    for i in data_625:
        await update(int(i[0]), [int(i[1]), int(i[2])], "625")
    records_408.sort(key=second_value)
    records_625.sort(key=second_value)
    await update_file()
    await send_long_message(inter, [f"records_408: {records_408}\n"\
        f"records_625: {records_625}"], inter.user.id)
    await inter.response.edit_message(content="sent to your dm")


@bot.tree.command(name="leaderboard",
    description="lookie who's fastest at waiting until a certain time to send an emoji")
@app_commands.choices(lb=[
    app_commands.Choice(name="408", value="408"),
    app_commands.Choice(name="625", value="625")])
async def leaderboard(inter: discord.Interaction,
                      user: discord.User=None, lb: str|None=None) -> None:
    """prints the leaderboard

    Args:
        inter (discord.Interaction): default parameter
        user (discord.User): the user requested
        lb (str|None): the leaderboard requested, "408" or "625"
    """
    await inter.response.defer()
    user = None if user is None else user.id
    if lb is None:
        embed_408: list = await get_records(user, "408")
        embed_625: list = await get_records(user, "625")
        view_408 = Buttons(embed_408) if len(embed_408) > 1 else None
        await inter.edit_original_response(embed=embed_408[0], view=view_408)
        view_625 = Buttons(embed_625) if len(embed_625) > 1 else None
        await inter.channel.send(embed=embed_625[0], view=view_625)
    else:
        embed: list = await get_records(user, lb)
        view = Buttons(embed) if len(embed) > 1 else None
        await inter.edit_original_response(embed=embed[0], view=view)


@bot.tree.command(name="ping", description="bot's delay")
async def ping(inter: discord.Interaction) -> None:
    """returns bot's latency

    Args:
        inter (discord.Interaction): default parameter
    """
    await inter.response.defer()
    await inter.edit_original_response(content=
                                       f"408 bot has a delay of {round(bot.latency * 1000)}ms")


@bot.tree.context_menu(name="vote")
async def vote(inter: discord.Interaction, message: discord.Message) -> None:
    """reacts checks and x's on a message

    Args:
        inter (discord.Interaction): default parameter
        message (discord.Message): the message to react to
    """
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    print(f"\"{message.content}\" suggestion received")
    await inter.response.send_message(content="the selected message is voted on", ephemeral=True)


@bot.tree.command(name="sync", description="Owner only")
@app_commands.default_permissions()
@app_commands.guilds(WCB_ID)
async def sync(inter: discord.Interaction) -> None:
    """sync all the other functions

    Args:
        interaction (discord.Interaction): default parameter
    """
    await inter.response.defer(ephemeral=True)
    if inter.user.id == DEVELOPER:
        synced = await bot.tree.sync()
        await inter.edit_original_response(
            content=f"synced command {[synced[i].name for i in range(len(synced))]}")
    else:
        await inter.edit_original_response(content="hmm i dont think you are matt bro")


# BOT EVENTS
# sends hrishu leaderboard
@tasks.loop(time=CST_409)
async def leaderboard_308() -> None:
    """sends hrishu 408 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("hrishu 408", True)


# sends 408 leaderboard
@tasks.loop(time=PDT_409)
async def leaderboard_408() -> None:
    """sends 408 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("408", False)


# sends 625 leaderboard
@tasks.loop(time=PDT_626)
async def leaderboard_625() -> None:
    """sends 625 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("625", False)


# pings @408 ping at 4:08pm PDT
@tasks.loop(time=PDT_408)
async def send_408() -> None:
    """sends 408 ping
    """
    global medal
    await bot.wait_until_ready()
    medal = 0
    await CHANNEL_408.send(ROLE_408)
    await CHANNEL_408.send("get ready guys")
    print("sent 408 ping at " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))


# pings @408 ping at 4:08pm CST
@tasks.loop(time=CST_408)
async def send_hrishu() -> None:
    """sends hrishu 408 ping
    """
    await bot.wait_until_ready()
    global medal
    medal = 0
    await CHANNEL_408.send("<@1124542462682218600>")
    await CHANNEL_408.send("get ready hrishu")
    print("sent hrishu ping at " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))


# pings @408 ping at 4:08pm CST
@tasks.loop(time=PDT_625)
async def send_625() -> None:
    """sends 625 ping
    """
    await bot.wait_until_ready()
    global medal
    medal = 0
    await CHANNEL_408.send(ROLE_625)
    await CHANNEL_408.send("get ready guys")
    print("sent 625 ping at " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))


@bot.event
async def on_message(message: discord.Message) -> None:
    """checks if reacting is needed every time someone sends something in any server

    Args:
        message (discord.Message): the message to perform action on
    """
    if message.channel.id == CHANNEL_408_ID:
        if message.content == EMOJI_408 or message.content == EMOJI_625:
            text = EMOJI_TO_TEXT[message.content]
            t: datetime.datetime = message.created_at
            timestamp = [pdt_hm(str(t.hour) + ":" + str(t.minute)),
                         t.second * 1000 + round(t.microsecond / 1000)]
            print(f"a {text} emoji was sent at {timestamp[0]}:{s_ms(timestamp[1])}")
            if pdt_h(t.hour) == "15" and message.content == EMOJI_408:
                await react(message, timestamp, LIST_HRISHU)
            elif pdt_h(t.hour) == "16" and message.content == EMOJI_408:
                await react(message, timestamp, LIST_408)
            elif pdt_h(t.hour) == "18" and message.content == EMOJI_625:
                await react(message, timestamp, LIST_625)
            else:
                await react(message, timestamp)
    elif message.channel.id == CHANNEL_SUGGESTIONS:
        if message.content[0] == "*":
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            print(f"\"{message.content}\" suggestion received")


# starts the bot
@bot.event
async def on_ready() -> None:
    """initiates the bot
    """
    global CHANNEL_408
    print(f"{bot.user} is now online!\ntime: " +
          datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))
    if not send_408.is_running():
        send_408.start()
        print("started 408")
    if not send_hrishu.is_running():
        send_hrishu.start()
        print("started hrishu")
    if not send_625.is_running():
        send_625.start()
        print("started 625")
    if not leaderboard_308.is_running():
        leaderboard_308.start()
        print("started leaderboard hrishu 408")
    if not leaderboard_408.is_running():
        leaderboard_408.start()
        print("started leaderboard 408")
    if not leaderboard_625.is_running():
        leaderboard_625.start()
        print("started leaderboard 625")
    synced = await bot.tree.sync(guild=bot.get_guild(WCB_ID))
    print(f"synced command {[synced[i].name for i in range(len(synced))]}")
    file = shelve.open("data")
    if "408" in list(file.keys()):
        global records_408
        records_408 = file["408"]
    if "625" in list(file.keys()):
        global records_625
        records_625 = file["625"]
    CHANNEL_408 = bot.get_channel(CHANNEL_408_ID)


bot.run(TOKEN)
