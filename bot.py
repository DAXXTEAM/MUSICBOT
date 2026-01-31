#!/usr/bin/env python3
import os, asyncio, logging, re
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, Update
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pytgcalls.exceptions import GroupCallNotFound
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION = os.getenv("SESSION_STRING")
LOG_GROUP = int(os.getenv("LOG_GROUP_ID", "0"))

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
calls = PyTgCalls(user)

queues = {}
active = {}
downloads_dir = "/tmp/music_cache"
os.makedirs(downloads_dir, exist_ok=True)

def format_duration(sec):
    if not sec: return "Live"
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"

def clean_artist(title, uploader):
    patterns = [r'^(.+?)\s*[-–—]\s*(.+)$', r'^(.+?)\s*[:|]\s*(.+)$']
    for p in patterns:
        match = re.match(p, title)
        if match:
            return re.sub(r'\s*(official|video|audio).*$', '', match.group(1), flags=re.IGNORECASE).strip()
    if uploader:
        return re.sub(r'\s*(music|vevo|official).*$', '', uploader, flags=re.IGNORECASE).strip()
    return "Unknown"

def download_audio(q):
    opts = {
        'format': 'bestaudio',
        'outtmpl': f'{downloads_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }
    search = f'ytsearch:{q}' if not q.startswith('http') else q
    with yt_dlp.YoutubeDL(opts) as ydl:
        i = ydl.extract_info(search, download=True)
        if 'entries' in i: i = i['entries'][0]
        filename = ydl.prepare_filename(i).rsplit('.', 1)[0] + '.mp3'
        return {
            'file': filename,
            'title': i.get('title', 'Unknown'),
            'artist': clean_artist(i.get('title', ''), i.get('uploader', '')),
            'duration': i.get('duration', 0),
            'thumb': i.get('thumbnail') or 'https://telegra.ph/file/2f7debf856695e0a17296.png',
            'webpage': i.get('webpage_url', '')
        }

async def ensure_assistant_joined(cid):
    try:
        await user.get_chat_member(cid, "me")
        return True
    except UserNotParticipant:
        try:
            link = await app.export_chat_invite_link(cid)
            await user.join_chat(link)
            await asyncio.sleep(2)
            return True
        except: return False
    except: return False

async def send_now_playing(cid, song, queue_list):
    caption = (
        "🎵 **𝐍𝐨𝐰 𝐏𝐥𝐚𝐲𝐢𝐧𝐠**\n\n"
        f"🎼 **𝐒𝐨𝐧𝐠 :** {song['title']}\n"
        f"🎙 **𝐀𝐫𝐭𝐢𝐬𝐭 :** {song['artist']}\n"
        f"⏳ **𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧 :** {format_duration(song['duration'])}\n"
        f"🙋‍♂️ **𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐁𝐲 :** {song['requester']}\n\n"
    )
    
    if queue_list:
        caption += "📋 **𝐔𝐩 𝐍𝐞𝐱𝐭:**\n\n"
        for i, s in enumerate(queue_list[:5], 1):
            caption += f"**{i}.** {s['title']}\n"
        if len(queue_list) > 5:
            caption += f"\n➕ _+{len(queue_list) - 5} more_"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏸", callback_data="pause"),
         InlineKeyboardButton("▶️", callback_data="resume")],
        [InlineKeyboardButton("⏭", callback_data="skip"),
         InlineKeyboardButton("⏹", callback_data="end")]
    ])
    
    try:
        if song.get('thumb'):
            await app.send_photo(cid, song['thumb'], caption=caption, reply_markup=buttons)
        else:
            await app.send_photo(cid, 'https://telegra.ph/file/2f7debf856695e0a17296.png', 
                                caption=caption, reply_markup=buttons)
    except Exception as e:
        logger.warning(f"Photo send failed: {e}, using text")
        await app.send_message(cid, caption, reply_markup=buttons)

async def play_next(cid):
    if cid not in queues or not queues[cid]:
        logger.info(f"Queue empty in {cid}")
        return
    
    s = queues[cid].pop(0)
    try:
        stream = AudioPiped(s['file'], HighQualityAudio())
        await calls.change_stream(cid, stream)
        active[cid] = s
        await send_now_playing(cid, s, queues.get(cid, []))
        logger.info(f"Playing: {s['title']}")
    except Exception as e:
        logger.error(f"Play next error: {e}")
        await play_next(cid)

@app.on_callback_query()
async def callback_handler(_, query: CallbackQuery):
    data = query.data
    cid = query.message.chat.id
    
    if data == "pause":
        try:
            await calls.pause_stream(cid)
            await query.answer("⏸ Paused", show_alert=False)
        except:
            await query.answer("❌ Can't pause", show_alert=True)
    
    elif data == "resume":
        try:
            await calls.resume_stream(cid)
            await query.answer("▶️ Resumed", show_alert=False)
        except:
            await query.answer("❌ Can't resume", show_alert=True)
    
    elif data == "skip":
        if cid in active:
            await query.answer("⏭ Skipping...", show_alert=False)
            await play_next(cid)
        else:
            await query.answer("❌ Nothing playing", show_alert=True)
    
    elif data == "end":
        try:
            await calls.leave_group_call(cid)
            if cid in queues: queues[cid].clear()
            if cid in active: del active[cid]
            await query.answer("⏹ Stopped", show_alert=False)
            await query.message.edit_caption("⏹ **Stopped**")
        except:
            await query.answer("❌ Not in call", show_alert=True)

@app.on_message(filters.command("start"))
async def start(_, m: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add To Group", url="https://t.me/MUSlCXBOT?startgroup=true")],
        [InlineKeyboardButton("📚 Commands", callback_data="help"),
         InlineKeyboardButton("👤 Owner", url="https://t.me/Vclub_Tech")]
    ])
    
    text = (
        "🎵 **𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐌𝐮𝐬𝐢𝐜 𝐁𝐨𝐭!**\n\n"
        "Play unlimited high-quality music in voice chats! 🎧\n\n"
        "**✨ 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:**\n"
        "🎧 High Quality Audio (320kbps)\n"
        "🚀 Fast & Stable\n"
        "📋 Queue Management\n"
        "⚡ Easy Inline Controls\n"
        "🔄 Auto Join\n\n"
        "**📝 𝐇𝐨𝐰 𝐓𝐨 𝐔𝐬𝐞:**\n"
        "1️⃣ Add bot to group\n"
        "2️⃣ Make admin (Invite Users)\n"
        "3️⃣ Start voice chat\n"
        "4️⃣ Send `/play [song name]`\n\n"
        "**🎯 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:**\n"
        "• `/play [song]` - Play music\n"
        "• `/skip` - Skip song\n"
        "• `/pause` - Pause\n"
        "• `/resume` - Resume\n"
        "• `/stop` - Stop\n"
        "• `/queue` - Queue\n\n"
        "Made with ❤️ by @Vclub_Tech"
    )
    
    try:
        await m.reply_photo("https://telegra.ph/file/2f7debf856695e0a17296.png", 
                          caption=text, reply_markup=buttons)
    except:
        await m.reply(text, reply_markup=buttons)

@app.on_callback_query(filters.regex("help"))
async def help_cb(_, q: CallbackQuery):
    await q.answer()
    help_text = (
        "📚 **𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬 𝐆𝐮𝐢𝐝𝐞**\n\n"
        "**🎵 Playback:**\n"
        "`/play [song or link]`\n"
        "_Example: /play shape of you_\n\n"
        "**⚙️ Controls:**\n"
        "`/pause` - Pause\n"
        "`/resume` - Resume\n"
        "`/skip` - Skip\n"
        "`/stop` or `/end` - Stop\n\n"
        "**📋 Queue:**\n"
        "`/queue` - View queue\n\n"
        "**💡 Tips:**\n"
        "• Use YouTube links\n"
        "• Use inline buttons\n"
        "• Bot stays in call\n\n"
        "Contact: @Vclub_Tech"
    )
    await q.message.reply(help_text)

@app.on_message(filters.command("play"))
async def play(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("❌ `/play [song]`")
    
    q = m.text.split(None, 1)[1]
    cid = m.chat.id
    msg = await m.reply("🔍 **Searching...**")
    
    try:
        if m.chat.type in ["group", "supergroup"]:
            if not await ensure_assistant_joined(cid):
                return await msg.edit("❌ Make bot admin!")
        
        await msg.edit("⬇️ **Downloading...**")
        song = await asyncio.to_thread(download_audio, q)
        song['requester'] = m.from_user.mention if m.from_user else "Anonymous"
        
        if cid not in queues: queues[cid] = []
        
        if cid not in active:
            try:
                stream = AudioPiped(song['file'], HighQualityAudio())
                await calls.join_group_call(cid, stream)
                active[cid] = song
                await msg.delete()
                await send_now_playing(cid, song, [])
                logger.info(f"Started: {song['title']}")
            except GroupCallNotFound:
                await msg.edit("❌ **Start voice chat!** 📞")
            except Exception as e:
                logger.error(f"Play error: {e}")
                await msg.edit(f"❌ {e}")
        else:
            queues[cid].append(song)
            await msg.edit(f"➕ **Queued:** {song['title'][:50]}\n📍 Position: {len(queues[cid])}")
    except Exception as e:
        logger.error(f"Command error: {e}")
        await msg.edit(f"❌ {str(e)[:100]}")

@app.on_message(filters.command("skip"))
async def skip(_, m: Message):
    if m.chat.id in active:
        await m.reply("⏭ **Skipped!**")
        await play_next(m.chat.id)
    else:
        await m.reply("❌ **Not playing**")

@app.on_message(filters.command("pause"))
async def pause(_, m: Message):
    try:
        await calls.pause_stream(m.chat.id)
        await m.reply("⏸ **Paused**")
    except: await m.reply("❌ **Not playing**")

@app.on_message(filters.command("resume"))
async def resume(_, m: Message):
    try:
        await calls.resume_stream(m.chat.id)
        await m.reply("▶️ **Resumed**")
    except: await m.reply("❌ **Not paused**")

@app.on_message(filters.command(["stop", "end"]))
async def stop(_, m: Message):
    cid = m.chat.id
    try:
        await calls.leave_group_call(cid)
        if cid in queues: queues[cid].clear()
        if cid in active: del active[cid]
        await m.reply("⏹ **Stopped**")
    except: await m.reply("❌ **Not in call**")

@app.on_message(filters.command("queue"))
async def queue(_, m: Message):
    if m.chat.id not in active: 
        return await m.reply("📭 **Nothing playing**")
    text = "📋 **QUEUE**\n\n"
    if m.chat.id in queues and queues[m.chat.id]:
        for i, s in enumerate(queues[m.chat.id], 1):
            text += f"**{i}.** {s['title']}\n"
    else:
        text += "📭 _Empty_"
    await m.reply(text)

@calls.on_stream_end()
async def on_end(_, u: Update):
    logger.info(f"Stream ended in {u.chat_id}")
    await play_next(u.chat_id)

async def main():
    await app.start()
    await user.start()
    await calls.start()
    logger.info("🎵 LIVE!")
    await idle()

if __name__ == "__main__":
    app.run(main())
