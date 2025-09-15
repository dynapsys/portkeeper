# portkeeper


Zrobiłem dla Ciebie bibliotekę i zapisałem ją jako pojedynczy plik Python (`portkeeper.py`) na kanwie — możesz go teraz otworzyć i przetestować. Krótkie podsumowanie tego, co zawiera i jak używać:

# Co zawiera

* `PortRegistry` — główna klasa do rezerwowania portów, zwalniania ich, oraz do zapisu/aktualizacji plików `.env` i `config.json`.
* Mechanizm lokalnego rejestru (`.port_registry.json`) i prostego pliku blokady, żeby uniknąć wyścigów przy jednoczesnych rezerwacjach.
* Opcja `hold=True` — jeśli chcesz fizycznie zablokować port, biblioteka może otworzyć gniazdo i je trzymać (w tle) aż do `release()`; przydatne gdy potrzebujesz pewności, że nikt inny nie zajmie portu.
* Atomowe zapisy plików (tmp -> replace) przy aktualizacji `.env` i `config.json`. Tworzy kopię zapasową `config.json` przed nadpisaniem (opcjonalnie).
* Mały CLI (`python portkeeper.py reserve ...` / `release`) do szybkiego testu.

# Szybkie przykłady użycia

Programowo (kontekst menadżera):

```py
from portkeeper import PortRegistry

reg = PortRegistry()

# zarezerwuj dowolny (ephemeral) port i trzymaj go w tle
with reg.reserve_context(preferred=8000, hold=True, owner='my-service') as res:
    print('port:', res.port)
    reg.write_env({'PORT': str(res.port)}, path='.env')
    # uruchom server, używając PORT z .env lub bezpośrednio res.port
# po wyjściu z contextu port jest zwalniany
```

CLI:

```
# zarezerwuj (spróbuje 8000, jeśli wolny; albo wykryje wolny)
python portkeeper.py reserve --preferred 8000 --hold --write-env PORT

# zwolnij port (usuwa wpis z registry)
python portkeeper.py release 8000
```
