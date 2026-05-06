import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": False
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
            return

        url = self.queue.pop(0)
        self.current = url

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info["url"]
            title = info["title"]

        source = await discord.FFmpegOpusAudio.from_probe(
            stream_url,
            **FFMPEG_OPTIONS
        )

        interaction.guild.voice_client.play(
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
            await interaction.followup.send("Entre em um canal de voz.")
            return

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        self.queue.append(url)

        await interaction.followup.send("Adicionado à fila.")

        vc = interaction.guild.voice_client
        if not vc.is_playing():
            await self.play_next(interaction)

    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Pulado")

    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.pause()
            await interaction.response.send_message("⏸️ Pausado")

    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.resume()
            await interaction.response.send_message("▶️ Continuado")

    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        self.queue.clear()

        if vc:
            vc.stop()
            await vc.disconnect()

        await interaction.response.send_message("⏹️ Parado")

    @app_commands.command(name="queue")
    async def queue_cmd(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("Fila vazia.")
            return

        msg = "\n".join(
            [f"{i+1}. {song}" for i, song in enumerate(self.queue[:10])]
        )

        await interaction.response.send_message(f"Fila:\n{msg}")

    @app_commands.command(name="remove")
    async def remove(self, interaction: discord.Interaction, position: int):
        if 0 < position <= len(self.queue):
            removed = self.queue.pop(position - 1)
            await interaction.response.send_message(
                f"Removido: {removed}"
            )

    @app_commands.command(name="loop")
    async def loop_song(self, interaction: discord.Interaction):
        self.loop = not self.loop
        await interaction.response.send_message(
            f"Loop música: {self.loop}"
        )

    @app_commands.command(name="loopqueue")
    async def loop_queue_cmd(self, interaction: discord.Interaction):
        self.loop_queue = not self.loop_queue
        await interaction.response.send_message(
            f"Loop fila: {self.loop_queue}"
        )

    @app_commands.command(name="volume")
    async def volume_cmd(self, interaction: discord.Interaction, volume: int):
        self.volume = volume / 100
        await interaction.response.send_message(
            f"Volume ajustado: {volume}%"
        )

    @app_commands.command(name="nowplaying")
    async def nowplaying(self, interaction: discord.Interaction):
        if self.current:
            await interaction.response.send_message(
                f"Tocando agora: {self.current}"
            )
        else:
            await interaction.response.send_message("Nada tocando.")