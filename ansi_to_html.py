import re

def ansi_to_html(text):
    # Mappa codici ANSI a stili CSS
    ansi_map = {
        '\033[91m': '<span style="color:red;">',
        '\033[92m': '<span style="color:green;">',
        '\033[93m': '<span style="color:orange;">',
        '\033[94m': '<span style="color:blue;">',
        '\033[1m': '<b>',
        '\033[0m': '</span></b>',
    }

    # Sostituisci i codici ANSI con HTML
    for ansi, html in ansi_map.items():
        text = text.replace(ansi, html)

    # Rimuovi eventuali codici ANSI residui
    text = re.sub(r'\033\[[0-9;]*m', '', text)

    return text


def remove_ansi_codes(text):
    return re.sub(r'\033\[[0-9;]*m', '', text)
