from functions.functions import My_message
from TelegramClient import Jarvis_client
from modules.valutes.settings import PATH
from config import jarvis_all, data_users
from cbrf.models import DailyCurrenciesRates
from core import cache_with_expiration
import requests, re
import collections

status = True

currency = {
    "доллар": "R01235",
    "евро": "R01239",
    "рубл": "",
    "бат": "R01675",
    "фунт": "R01035",
    "йена": "R01820",
    "франк": "R01775",
    "юань": "R01375",
    "лира": "R01700"
}

crypto = {
    "биткоин": "bitcoin",
    "эфир": "ethereum",
    "тон": "the-open-network",
    "лайткоин": "litecoin",
    "рипл": "xrp",
    "кардано": "cardano",
    "солана": "solana",
    "догекоин": "dogecoin"
}

c_info = DailyCurrenciesRates()

@cache_with_expiration(6 * 60 * 60)
def get_crypto_price(crypto_id, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies={vs_currency}&include_24hr_change=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data[crypto_id][vs_currency]), float(data[crypto_id]["usd_24h_change"])
    else:
        return None, None

def find_currencies(text):
    all_currencies = {**currency, **crypto}
    pattern = (
        r'(?P<integer>\d{1,3}(?:[\s.,]\d{3})*|два|три|четыре|пять|шесть|семь|восемь|девять)'
        r'(?:[\.,](?P<fraction>\d{1,2}))?'
        r'\s*(?P<currency>' + '|'.join(re.escape(cur) for cur in all_currencies.keys()) + r')'
    )
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    results = {}

    word_to_num = {
        'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
        'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9
    }

    for match in matches:
        integer_word = match.group('integer').lower()
        integer_part = word_to_num.get(integer_word, re.sub(r'[\s.,]', '', integer_word))
        fraction_part = match.group('fraction') or '00'
        amount = float(f"{integer_part}.{fraction_part.ljust(2, '0')}")
        current_currency = match.group('currency').lower()
        
        if current_currency in results:
            results[current_currency]['amount'] += amount
        else:
            currency_type = 'currency' if current_currency in currency else 'crypto'
            code = all_currencies[current_currency]
            results[current_currency] = {
                'amount': amount,
                'type': currency_type,
                'code': code
            }
    
    return results if results else None

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]["status"]:
        return
    
    message = new_message.message
    text = message.text.lower()
    
    if "курс" == text.split()[0]:
        for item in currency:
            if item in text:
                usd = float(c_info.get_by_id("R01235").value)
                price = 1.0 if not currency[item] else float(c_info.get_by_id(currency[item]).value)
                text_answer = f"Курс {text.replace('курс', '')}.\n\nЦена:\n"
                usd1 = price / usd
                euro = price / float(c_info.get_by_id('R01239').value)
                text_answer += f"<b>• {price:,.2f}₽</b>\n" if price != 1.0 else ""
                text_answer += f"<b>• {usd1:,.2f}$</b>\n" if usd1 != 1.0 else ""
                text_answer += f"<b>• {euro:,.2f}€</b>\n" if euro != 1.0 else ""
                return await jarvis.send_message(message, text_answer.replace(",", " "))
        
        for item in crypto:
            if item in text:
                usd_rate = float(c_info.get_by_id("R01235").value)
                price, percent = get_crypto_price(crypto[item])
                text_answer = (
                    f"Курс {text.replace('курс', '')}. "
                    f"Изменение за 24ч: <b>{'+' if percent > 0 else ''}{percent:,.2f}%</b>\n\n"
                    f"Цена:\n"
                    f"<b>• {price:,.2f}$</b>\n"
                    f"<b>• {price * usd_rate:,.2f}₽</b>\n"
                    f"<b>• {(price * usd_rate)/float(c_info.get_by_id('R01239').value):,.2f}€</b>\n\n"
                    f"В криптовалютах:\n"
                )
                
                # Добавляем конвертацию в другие криптовалюты
                for crypto_name, crypto_id in crypto.items():
                    if crypto_name == item:
                        continue
                    crypto_price, _ = get_crypto_price(crypto_id)
                    if crypto_price:
                        amount = price / crypto_price
                        text_answer += f"<b>• {amount:,.8f} {crypto_name}</b>\n"
                
                return await jarvis.send_message(message, text_answer.replace(",", " "))

    if jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]["status_auto"]:
        res = find_currencies(text)
        if res:
            text_answer = ""
            usd_rate = float(c_info.get_by_id("R01235").value)
            euro_rate = float(c_info.get_by_id('R01239').value)
            
            for item, data in res.items():
                original_amount = data['amount']
                currency_type = data['type']
                code = data['code']
                
                # Получаем базовый курс
                if currency_type == 'currency':
                    original_rate = 1.0 if not code else float(c_info.get_by_id(code).value)
                    rub_amount = original_amount * original_rate
                else:
                    crypto_price, _ = get_crypto_price(code)
                    rub_amount = original_amount * crypto_price * usd_rate
                
                # Конвертация в стандартные валюты
                conversions = {
                    'rub': round(rub_amount, 2),
                    'usd': round(rub_amount / usd_rate, 2),
                    'eur': round(rub_amount / euro_rate, 2),
                }
                
                # Конвертация в криптовалюты
                for crypto_name, crypto_id in crypto.items():
                    if crypto_name == item:
                        continue
                    crypto_price, _ = get_crypto_price(crypto_id)
                    if crypto_price:
                        crypto_amount = (rub_amount / usd_rate) / crypto_price
                        conversions[crypto_name] = round(crypto_amount, 8)
                
                # Формируем текст ответа
                text_answer += f"<b>{original_amount:,.2f} {item}</b> это:\n"
                for key, value in conversions.items():
                    if key == 'usd' and (currency_type == 'currency' and code == 'R01235'):
                        continue
                    if value == 0:
                        continue
                    symbol = {
                        'rub': '₽',
                        'eur': '€',
                        'биткоин': 'BTC',
                        'эфир': 'ETH',
                        'тон': 'TON',
                        'лайткоин': 'LTC',
                        'рипл': 'XRP',
                        'кардано': 'ADA',
                        'солана': 'SOL',
                        'догекоин': 'DOGE'
                    }.get(key, '')
                    text_answer += f"<b>• {value:,.2f}{symbol}</b>\n" if symbol else f"<b>• {value:,.8f} {key}</b>\n"
                
                text_answer = text_answer.replace(",", " ")
            
            await jarvis.send_message(message, text_answer)