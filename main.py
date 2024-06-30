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
CHANNEL_408: discord.TextChannel = bot.get_channel(CHANNEL_408_ID)
TEST_SERVER_ID = 1240098098513055776
WCB_ID = 1204222579498557440
DEVELOPER = 1104220935973777459
LIST_408 = [16, 8]
LIST_HRISHU = [15, 8]
LIST_625 = [18, 25]

# variables
medal: int
users: list = []
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


def valid_num(num: int) -> str:
    """adds 0 before a one-digit number

    Args:
        num (int): number to be modified

    Returns:
        str: the resultant string
    """
    return str(num) if num >= 10 else "0" + str(num)
    # either ~ 02 or 10


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


async def update(author: int, speed: list, time: str) -> None:
    """updates the records list

    Args:
        author (int): the id of the person who got the time
        speed (list): a list of the time they achieved in ms, and the message id
        time (str): the time of the day (408 or 625)
    """
    if time == "408":
        global records_408
        records_408.sort(key=second_value)
        if speed[0] <= records_408[-1][1] or len(records_408) < 10:
            records_408.append([author, speed[0], speed[1]])
    elif time == "625":
        global records_625
        records_625.sort(key=second_value)
        if speed[0] <= records_625[-1][1] or len(records_625) < 10:
            records_625.append([author, speed[0], speed[1]])


async def react(message: discord.Message, timestamp: list, t: list = None):
    """react to the given message with different emojis

    Args:
        message (discord.Message): the message to react to
        timestamp (list): the time the message was sent at
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
            need_to_react.append([message, timestamp[1]])
            sleep(min(bot.latency, 0.5))
            medal += 1
            copy = medal
            need_to_react.sort(key=second_value)
            await need_to_react.pop(0)[0].add_reaction(RANKING_TO_EMOJI[copy])
            print(f"reacted with {RANKING_TO_EMOJI[copy]}")
            # adds the user id to a list, along with the ms
            users.append([message.author.id, timestamp[1]])
        elif timestamp[0] == t and (message.author.id in user_ids or medal >= 10):
            await message.add_reaction("🙂")
        elif timestamp[0] == plus or timestamp[0] == minus:
            await message.add_reaction("☠️")
        else:
            print(f"target time: {t}, sent time: {timestamp[0]}")
            await message.add_reaction("💀")


async def send_leaderboard(timestamp: str) -> None:
    """sends a specific leaderboard to #408

    Args:
        timestamp (str): a timestamp indicating which leaderboard to send
    """
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
        for i, [user, t] in enumerate(users, 1):
            await update(user, [t, msg.id], timestamp) #updates record
        update_file() #updates the file


async def update_file() -> None:
    """writes records_408 and records_625 to a file
    """
    file = shelve.open("data")
    file[408] = records_408
    file[625] = records_625
    file.close()

def get_records(t: str) -> discord.Embed:
    """returns the records of the server

    Args:
        t (str): 408 or 625

    Returns:
        discord.Embed: the embed to return
    """
    if t == "408" and records_408:
        records_408.sort(key=second_value)
        record = "\n".join([f"{i}. [{s_ms(val[0])}]"\
                            f"({CHANNEL_408.fetch_message(a)}): "\
                            f"{bot.get_user(key).mention()}" #e.g. 1. 0ms: @matt
                            for i, [key, val, a] in enumerate(records_408)])
            #key = user id, val = [time in ms, id to leaderboard sent]
    elif t == "625" and records_625: #625
        record = "\n".join([f"{i}. [{s_ms(val[0])}]"\
                            f"({CHANNEL_408.fetch_message(a)}): "\
                            f"{bot.get_user(key).mention()}" #see above
                            for i, [key, val, a] in enumerate(records_625)])
    else:
        record = "no data yet :)"
    return discord.Embed(
        title="Leaderboard:",
        description=record,
        color=discord.Color(65535)) #00ffff


# BOT COMMANDS
@bot.tree.command(name="feeddata", description="DANGEROUS: overrite the data of this server")
@app_commands.default_permissions()
async def feeddata(inter: discord.Interaction, data: str) -> None:
    """feed in the data for the server in a string

    Args:
        inter (discord.Interaction): default parameter
        data (str): the data to be processed
    """
    global records_408, records_625
    data = re.compile(r"408\s(.)\s625\s(.)").search(data)
    data_408 = re.compile(r"(\d+) (\d+) (\d+)\n").findall(data.group(1))
    data_625 = re.compile(r"(\d+) (\d+) (\d+)\n").findall(data.group(2))
    for i in data_408:
        records_408.append([i[0], i[1], i[2]])
    for i in data_625:
        records_625.append([i[0], i[1], i[2]])
    file = shelve.open("data")
    file[408] = records_408
    file[625] = records_625
    file.close()
    await inter.response.send_message(f"records_408: {records_408}\nrecords_625: {records_625}", ephemeral=True)


@bot.tree.command(name="leaderboard",
    description="lookie who's fastest at waiting until a certain time to send an emoji")
@app_commands.choices(lb=[
    app_commands.Choice(name="408", value="408"),
    app_commands.Choice(name="625", value="625")])
async def leaderboard(inter: discord.Interaction, lb: str) -> None:
    """prints the leaderboard

    Args:
        inter (discord.Interaction): default parameter
    """
    await inter.response.send_message(embed=get_records(lb))


@bot.tree.command(name="ping", description="bot's delay")
async def ping(inter: discord.Interaction) -> None:
    """returns bot's latency

    Args:
        inter (discord.Interaction): default parameter
    """
    await inter.response.send_message(f"408 bot has a delay of {round(bot.latency * 1000)}ms")


@bot.tree.command(name="sync", description="Owner only")
@app_commands.guilds(WCB_ID)
async def sync(inter: discord.Interaction) -> None:
    """sync all the other functions

    Args:
        interaction (discord.Interaction): default parameter
    """
    if inter.user.id == DEVELOPER:
        synced = await bot.tree.sync()
        await inter.response.send_message(
            f"synced command {[synced[i].name for i in range(len(synced))]}",
                                                ephemeral=True)
    else:
        await inter.response.send_message("hmm i dont think you are matt bro", ephemeral=True)


# BOT EVENTS
# sends 408 leaderboard
@tasks.loop(time=PDT_409)
async def leaderboard_408() -> None:
    """sends 408 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("408")

# sends hrishu leaderboard
@tasks.loop(time=CST_409)
async def leaderboard_308() -> None:
    """sends hrishu 408 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("hrishu 408")


# sends 625 leaderboard
@tasks.loop(time=PDT_626)
async def leaderboard_625() -> None:
    """sends 625 leaderboard
    """
    await bot.wait_until_ready()
    await send_leaderboard("625")


# pings @408 ping at 4:08pm PDT
@tasks.loop(time=PDT_408)
async def send_408() -> None:
    """sends 408 ping
    """
    global medal, users
    await bot.wait_until_ready()
    medal = 0
    users = []
    await CHANNEL_408.send(ROLE_408)
    await CHANNEL_408.send("get ready guys")
    print("sent 408 ping at " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))


# pings @408 ping at 4:08pm CST
@tasks.loop(time=CST_408)
async def send_hrishu() -> None:
    """sends hrishu 408 ping
    """
    await bot.wait_until_ready()
    global medal, users
    medal = 0
    users = []
    await CHANNEL_408.send("<@1124542462682218600>")
    await CHANNEL_408.send("get ready hrishu")
    print("sent hrishu ping at " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))


# pings @408 ping at 4:08pm CST
@tasks.loop(time=PDT_625)
async def send_625() -> None:
    """sends 625 ping
    """
    await bot.wait_until_ready()
    global medal, users
    medal = 0
    users = []
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
            t = message.created_at
            timestamp = [pdt_hm(str(t.hour) + ":" + valid_num(t.minute)),
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


# starts the bot
@bot.event
async def on_ready() -> None:
    """initiates the bot
    """
    print(f"{bot.user} is now online!\ntime: " + datetime.datetime.now(PDT).strftime('%m-%d %H:%M:%S'))
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
    if 408 in list(file.keys()):
        global records_408
        records_408 = file[408]
    elif 625 in list(file.keys()):
        global records_625
        records_625 = file[625]


bot.run(TOKEN)
