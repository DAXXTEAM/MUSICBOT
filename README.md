# 🎵 Simple Music Bot

A powerful Telegram music bot that plays high-quality music in voice chats!

## ✨ Features

- 🎧 **High Quality Audio** - 320kbps MP3
- 🚀 **Fast & Stable** - Reliable playback
- 📋 **Queue Management** - Multiple songs queue
- ⚡ **Inline Controls** - Easy button controls
- 🔄 **Auto Join** - Bot joins automatically
- 🎯 **YouTube Support** - Play from YouTube
- 💾 **File Caching** - Faster repeated plays

## 📝 Commands

- `/start` - Start the bot
- `/play [song]` - Play a song
- `/skip` - Skip current song
- `/pause` - Pause playback
- `/resume` - Resume playback
- `/stop` or `/end` - Stop and leave
- `/queue` - Show queue

## 🚀 Deployment

### Requirements

- Python 3.10+
- FFmpeg
- Deno (for yt-dlp)

### Environment Variables

Create a `.env` file:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
SESSION_STRING=your_session_string
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/DAXXTEAM/simple-music-bot
cd simple-music-bot
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Install FFmpeg:
```bash
apt-get install -y ffmpeg
```

4. Install Deno:
```bash
curl -fsSL https://deno.land/install.sh | sh
export PATH="/root/.deno/bin:$PATH"
```

5. Generate session string:
```bash
python3 generate_session.py
```

6. Configure environment:
```bash
cp .env.example .env
# Edit .env with your values
```

7. Run the bot:
```bash
python3 bot.py
```

### Systemd Service (Optional)

```bash
sudo cp simple-music.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable simple-music
sudo systemctl start simple-music
```

## 📸 Screenshots

### Start Message
Beautiful welcome message with inline buttons

### Now Playing
Fancy UI with song info and control buttons

## 🛠️ Tech Stack

- **Pyrogram** - Telegram MTProto API
- **PyTgCalls** - Voice chat support
- **yt-dlp** - YouTube audio extraction
- **FFmpeg** - Audio processing

## 👨‍💻 Developer

Made with ❤️ by [@Vclub_Tech](https://t.me/Vclub_Tech)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit PRs.

## ⭐ Support

If you like this project, please give it a ⭐ on GitHub!
