# Ładowanie baterii laptopa

Miłosz Kurszewski s32230, Łukasz Burnicki s31052

Symulacja ładowania baterii w Pythonie z użyciem scikit-fuzzy.
Sterownik dobiera moc na podstawie poziomu baterii, temperatury i tempa
nagrzewania. Ładuje szybko, a przy nagrzewaniu i pod koniec zmniejsza moc.
Przy 45°C wstrzymuje ładowanie. Symulacja kończy się przy 100%.

Uruchomienie w terminalu projektu:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

W PyCharm wystarczy wybrać interpreter `.venv` i uruchomić `main.py`.
Jeden krok to minuta modelu. Wyniki pokazują się w terminalu.
Domyślne parametry to 20%, 28°C, bateria 60 Wh i moc ładowania 65 W.

Początkową temperaturę i poziom można zmienić, np.:

```powershell
.venv\Scripts\python.exe main.py --poziom 20 --temperatura 46
```
