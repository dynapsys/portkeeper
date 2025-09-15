# portkeeper Zagadnienia i uwagi

* Rejestracja w pliku JSON i próba bindowania portu pomagają wykryć dostępność, ale istnieje zawsze niewielkie okno wyścigu pomiędzy sprawdzeniem a użyciem portu przez inny proces. Jeśli potrzebujesz pełnej gwarancji, użyj `hold=True`, żeby trzymać socket otwarty przez cały czas uruchomienia Twojego serwera.
* Mechanizm lock-a używa `fcntl` na Unixach i `msvcrt` na Windows; jeśli oba są niedostępne używa prostej metody z plikiem `.lck`.
* Biblioteka jest jednofajlowym rozwiązaniem do szybkiego startu; można łatwo rozdzielić na moduły, dodać logowanie, rozszerzone zarządzanie właścicielami, TTL rezerwacji itp.


* Dodać przykładowe testy jednostkowe (pytest),
* Opakować bibliotekę jako paczkę (`setup.cfg`/`pyproject.toml`) i dodać entrypoint CLI,
* Rozszerzyć rejestr o TTL (automatyczne wygaszanie starych rezerwacji),
* Dodać wsparcie dla konfiguracji globalnej (np. katalog `.portkeeper/` w home),
* Dostosować sposób trzymania portu (np. proces pomocniczy zamiast wątku).

