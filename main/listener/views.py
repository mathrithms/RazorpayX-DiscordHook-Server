from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.utils.encoding import force_bytes
from hashlib import sha256
import hmac

import json
from discord_webhook import DiscordWebhook, DiscordEmbed

import os
from dotenv import load_dotenv

load_dotenv('../../.env')

@require_POST
@csrf_exempt
def webhook(request):
    raw_body = request.body
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET')
    webhook_signature = request.headers.get('X-Razorpay-Signature')

    if webhook_signature is None:
        return HttpResponseForbidden('Permission denied.')
    
    sha_name, signature = webhook_signature.split('=')
    if sha_name != 'sha256':
        return HttpResponseServerError('Operation not supported.', status=501)

    mac = hmac.new(force_bytes(webhook_secret), msg=force_bytes(raw_body), digestmod=sha256)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden('Permission denied.')

    body = json.loads(str(request.body, encoding='utf-8'))
    event = body["event"]

    webhook_url = os.getenv('DISCORD_WEBHOOK_CHANNEL_URL')
    webhook = DiscordWebhook(url=webhook_url)

    entity = body['contains'][0]
    if entity == "payout":
        color = "00FF00"
        if body['payload']['payout']['entity']['error']['description'] is not None or body['payload']['payout']['entity']['status'] == 'failed' or body['payload']['payout']['entity']['status'] == 'rejected':
            color = "FF0000"

        embed = DiscordEmbed(title = f"{' '.join(event.split('.')).upper()}", description = f"This webhook is triggered by the {event} event", color = color)
        embed.set_author(
            name = "RazorpayX"
        )

        embed.add_embed_field(name = "Account ID", value=f"```{body['account_id']}```")
        embed.add_embed_field(name = "Amount", value=f"```{body['payload']['payout']['entity']['currency']} {body['payload']['payout']['entity']['amount']}```")
        embed.add_embed_field(name = "Mode", value=f"```{body['payload']['payout']['entity']['mode'].upper()}```")
        webhook.add_embed(embed=embed)
        webhook.execute()
    
    elif entity == "transaction":
        color = "00FF00"

        embed = DiscordEmbed(title = f"{' '.join(event.split('.')).upper()}", description = f"This webhook is triggered by the {event} event", color = color)
        embed.set_author(
            name = "RazorpayX"
        )

        embed.add_embed_field(name = "Account ID", value=f"```{body['account_id']}```")
        embed.add_embed_field(name = "Amount", value=f"```{body['payload']['transaction']['entity']['currency']} {body['payload']['transaction']['entity']['amount']}```")
        embed.add_embed_field(name = "Account No.", value=f"```{body['payload']['transaction']['entity']['account_number']}```")
        embed.add_embed_field(name = "Mode", value=f"```{body['payload']['transaction']['entity']['source']['mode'].upper()}```")
        embed.add_embed_field(name = "Balance", value=f"```{body['payload']['transaction']['entity']['currency']} {body['payload']['transaction']['entity']['balance']}```")
        webhook.add_embed(embed=embed)
        webhook.execute()
    
    else:
        return HttpResponse(status=204)

    return HttpResponse(f"{' '.join(event.split('.')).upper()}")
