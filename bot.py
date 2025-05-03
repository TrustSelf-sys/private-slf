import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import random
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Lista de IDs permitidos (dono do bot ou usuário com permissão)
IDS_PERMITIDOS = [1025782686624780381, 1056705326352715787]  # IDs já permitidos

# Definindo o ID do dono do bot (o único que pode adicionar permissões)
ID_DONO = 1249477991747293266 # Substitua com o seu ID

grudados = {}
blacklist = {}

def parse_tempo(tempo_str):
    match = re.match(r"(\d+)([smh])", tempo_str)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    return None

# Função para verificar se o usuário tem permissão
async def verificar_permissao(interaction: discord.Interaction):
    if interaction.user.id not in IDS_PERMITIDOS:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return False
    return True

# Função para verificar se o usuário é o dono do bot
async def verificar_se_dono(interaction: discord.Interaction):
    if interaction.user.id != ID_DONO:
        await interaction.response.send_message("Você não tem permissão para adicionar IDs.", ephemeral=True)
        return False
    return True

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

     # Define status do bot
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name="Feito por: andre = uwsf")
    )


    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@tree.command(name="dar_permissao", description="Dá permissão a um usuário para usar o bot.")
@app_commands.describe(usuario="Usuário para adicionar permissão")
async def dar_permissao(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_se_dono(interaction):  # Verificação de permissão para o dono
        return

    if usuario.id in IDS_PERMITIDOS:
        await interaction.response.send_message(f"{usuario.display_name} já tem permissão.", ephemeral=True)
        return

    IDS_PERMITIDOS.append(usuario.id)
    await interaction.response.send_message(f"{usuario.display_name} agora tem permissão para usar o bot.", ephemeral=True)

@tree.command(name="remover_permissao", description="Remove a permissão de um usuário para usar o bot.")
@app_commands.describe(usuario="Usuário para remover permissão")
async def remover_permissao(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_se_dono(interaction):  # Verificação de permissão para o dono
        return

    if usuario.id not in IDS_PERMITIDOS:
        await interaction.response.send_message(f"{usuario.display_name} não tem permissão.", ephemeral=True)
        return

    IDS_PERMITIDOS.remove(usuario.id)
    await interaction.response.send_message(f"A permissão de {usuario.display_name} foi removida.", ephemeral=True)

@tree.command(name="grudar", description="Gruda um usuário a você até você desgrudar.")
@app_commands.describe(usuario="Usuário para seguir você")
async def grudar(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_permissao(interaction):  # Verificação de permissão
        return

    if usuario.id in grudados:
        await interaction.response.send_message("Esse usuário já está grudado em alguém.", ephemeral=True)
        return

    grudados[usuario.id] = interaction.user.id

    # Verifica se o usuário está em um canal de voz e move ele para o canal onde você está
    if interaction.user.voice and interaction.user.voice.channel:
        try:
            await usuario.move_to(interaction.user.voice.channel)  # Move o usuário para o canal de voz onde você está
            await interaction.response.send_message(f"{usuario.display_name} agora está grudado em você.", ephemeral=True)
        except discord.errors.HTTPException:
            await interaction.response.send_message("Não foi possível mover o usuário. Tente novamente mais tarde.", ephemeral=True)
    else:
        await interaction.response.send_message("Você não está em nenhum canal de voz no momento.", ephemeral=True)

@tree.command(name="desgrudar", description="Remove o grudar de um usuário.")
@app_commands.describe(usuario="Usuário para desgrudar")
async def desgrudar(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_permissao(interaction):  # Verificação de permissão
        return

    if grudados.pop(usuario.id, None):
        await interaction.response.send_message(f"{usuario.display_name} foi desgrudado.", ephemeral=True)
    else:
        await interaction.response.send_message("Esse usuário não estava grudado.", ephemeral=True)

# Aqui é onde você adiciona o evento on_voice_state_update
@bot.event
async def on_voice_state_update(member, before, after):
    # Verifica se o membro estava grudado em alguém e saiu do canal
    if member.id in grudados:
        # Verifica se o membro saiu do canal de voz
        if after.channel is None:  # O membro saiu do canal
            lider_id = grudados[member.id]
            lider = member.guild.get_member(lider_id)
            if lider and lider.voice and lider.voice.channel:  # Verifica se o "líder" ainda está em um canal de voz
                try:
                    # Move o membro para o canal de voz do "líder"
                    await member.move_to(lider.voice.channel)
                except discord.errors.HTTPException:
                    pass  # Se não conseguir mover, não faz nada
                
@tree.command(name="blacklist_call", description="Impede um usuário de entrar em canais de voz por um tempo.")
@app_commands.describe(usuario="Usuário", tempo="Tempo: ex. 30s, 2m, 1h")
async def blacklist_call(interaction: discord.Interaction, usuario: discord.Member, tempo: str):
    if not await verificar_permissao(interaction):  # Verificação de permissão
        return

    duration = parse_tempo(tempo)
    if not duration:
        await interaction.response.send_message("Formato de tempo inválido. Use s, m ou h. Ex: 30s, 2m, 1h", ephemeral=True)
        return

    fim = datetime.utcnow() + duration
    blacklist[usuario.id] = fim

    # Desconecta se o usuário estiver em um canal de voz
    if usuario.voice and usuario.voice.channel:
        try:
            await usuario.move_to(None)  # Desconecta o usuário
            await usuario.send("Você foi desconectado devido à blacklist e não poderá entrar em canais de voz.")
        except:
            pass

    await interaction.response.send_message(f"{usuario.display_name} foi adicionado à blacklist por {tempo}.", ephemeral=True)

@tree.command(name="remover_blacklist", description="Remove um usuário da blacklist de chamadas.")
@app_commands.describe(usuario="Usuário para remover da blacklist")
async def remover_blacklist(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_permissao(interaction):  # Verificação de permissão
        return

    if blacklist.pop(usuario.id, None):
        await interaction.response.send_message(f"{usuario.display_name} removido da blacklist.", ephemeral=True)
    else:
        await interaction.response.send_message("Esse usuário não está na blacklist.", ephemeral=True)

@tree.command(name="andar", description="Move o usuário aleatoriamente entre canais de voz por 30 segundos.")
@app_commands.describe(usuario="Usuário para mover aleatoriamente")
async def andar(interaction: discord.Interaction, usuario: discord.Member):
    if not await verificar_permissao(interaction):  # Verificação de permissão
        return

    canais_voz = [c for c in interaction.guild.voice_channels if c.permissions_for(usuario).connect]
    if not canais_voz:
        await interaction.response.send_message("Não há canais de voz disponíveis para mover o usuário.", ephemeral=True)
        return

    await interaction.response.send_message(f"Movendo {usuario.display_name} aleatoriamente por 30 segundos.", ephemeral=True)

    fim = asyncio.get_event_loop().time() + 30
    while asyncio.get_event_loop().time() < fim:
        canal = random.choice(canais_voz)
        try:
            await usuario.move_to(canal)
        except:
            pass
        await asyncio.sleep(0.2)  # Mais rápido

@bot.event
async def on_voice_state_update(member, before, after):
    # Blacklist ativa
    if member.id in blacklist:
        if datetime.utcnow() < blacklist[member.id]:
            if after.channel:
                await member.move_to(None)
                try:
                    await member.send("Você está temporariamente proibido de entrar em canais de voz.")
                except:
                    pass
        else:
            del blacklist[member.id]

    # Grudar automático
    for seguido_id, lider_id in grudados.items():
        if lider_id == member.id:
            seguido = member.guild.get_member(seguido_id)
            if seguido and member.voice and member.voice.channel:
                try:
                    await seguido.move_to(member.voice.channel)
                except:
                    pass

bot.run("TOKEN BOT")
