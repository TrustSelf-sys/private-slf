# Discord Voice Bot

Bot de Discord com os seguintes comandos de barra:

## Comandos

- `/grudar @usuário` → Faz o usuário seguir você até usar /desgrudar.
- `/desgrudar @usuário` → Para o efeito de seguir.
- `/blacklist_call @usuário tempo` → Impede o usuário de entrar em canais de voz. Ex: 30s, 2m, 1h
- `/remover_blacklist @usuário` → Libera o acesso ao canal de voz.
- `/andar @usuário` → Move aleatoriamente o usuário entre canais por 30 segundos.

## Instalação

```bash
pip install -r requirements.txt
python bot.py
```

Não se esqueça de ativar os intents no portal do Discord:
- Presença
- Membros
- Conteúdo das mensagens (Message Content)
