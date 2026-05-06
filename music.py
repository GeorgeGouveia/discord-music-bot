import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "extract_flat": False,
    "cookiefile": "cookies.txt",
    "extractor_args": {
        "youtube": {
            "player_client": ["web"]
        }
    }
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current = None
        self.loop = False
        self.loop_queue = False
        self.volume = 0.5

    async def play_next(self, interaction):
        if self.loop and self.current:
            self.queue.insert(0, self.current)

        elif self.loop_queue and self.current:
            self.queue.append(self.current)

        if len(self.queue) == 0:
            self.current = None
            return

        url = self.queue.pop(0)
        self.current = url

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)

                if "entries" in info:
                    info = info["entries"][0]

                stream_url = info["url"]
                title = info["title"]

        except Exception as e:
            print(f"Erro yt-dlp: {e}")
            await interaction.channel.send(
                "❌ Não consegui carregar essa música. "
                "YouTube pode ter bloqueado ou link inválido."
            )

            await self.play_next(interaction)
            return

        source = await discord.FFmpegOpusAudio.from_probe(
            stream_url,
            **FFMPEG_OPTIONS
        )

        vc = interaction.guild.voice_client

        vc.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction),
                self.bot.loop
            )
        )

        await interaction.channel.send(f"🎵 Tocando: {title}")

    @app_commands.command(name="play", description="Tocar música")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("❌ Entre em um canal de voz.")
            return

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        self.queue.append(url)

        await interaction.followup.send(f"✅ Adicionado à fila: {url}")

        vc = interaction.guild.voice_client
        if not vc.is_playing():
            await self.play_next(interaction)

    @app_commands.command(name="skip", description="Pular música")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Música pulada")
        else:
            await interaction.response.send_message("Nada tocando.")

    @app_commands.command(name="pause", description="Pausar música")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Música pausada")
        else:
            await interaction.response.send_message("Nada tocando.")

    @app_commands.command(name="resume", description="Continuar música")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Música retomada")
        else:
            await interaction.response.send_message("Nenhuma música pausada.")

    @app_commands.command(name="stop", description="Parar música")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        self.queue.clear()
        self.current = None

        if vc:
            vc.stop()
            await vc.disconnect()

        await interaction.response.send_message("⏹️ Player parado e desconectado.")

    @app_commands.command(name="queue", description="Mostrar fila")
    async def queue_cmd(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("📭 Fila vazia.")
            return

        msg = "\n".join(
            [f"{i+1}. {song}" for i, song in enumerate(self.queue[:10])]
        )

        await interaction.response.send_message(f"📜 Fila:\n{msg}")

    @app_commands.command(name="remove", description="Remover da fila")
    async def remove(self, interaction: discord.Interaction, position: int):
        if 0 < position <= len(self.queue):
            removed = self.queue.pop(position - 1)
            await interaction.response.send_message(
                f"🗑️ Removido da fila: {removed}"
            )
        else:
            await interaction.response.send_message("Posição inválida.")

    @app_commands.command(name="loop", description="Loop música atual")
    async def loop_song(self, interaction: discord.Interaction):
        self.loop = not self.loop
        await interaction.response.send_message(
            f"🔁 Loop música: {'ativado' if self.loop else 'desativado'}"
        )

    @app_commands.command(name="loopqueue", description="Loop fila")
    async def loop_queue_cmd(self, interaction: discord.Interaction):
        self.loop_queue = not self.loop_queue
        await interaction.response.send_message(
            f"🔂 Loop fila: {'ativado' if self.loop_queue else 'desativado'}"
        )

    @app_commands.command(name="nowplaying", description="Música atual")
    async def nowplaying(self, interaction: discord.Interaction):
        if self.current:
            await interaction.response.send_message(
                f"🎶 Tocando agora: {self.current}"
            )
        else:
            await interaction.response.send_message("Nada tocando.")


async def setup(bot):
    await bot.add_cog(Music(bot))