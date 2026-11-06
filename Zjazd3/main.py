"""Symulacja szybkiego ładowania baterii laptopa z logiką rozmytą.

Problem:
    Sterownik wybiera wysoką moc ładowania, dopóki pozwalają na to temperatura
    i poziom baterii. Zwalnia przy nagrzewaniu oraz pod koniec ładowania.
    Trzy wejścia to poziom baterii, temperatura i tempo jej wzrostu.

Autorzy:
    Miłosz Kurszewski (s32230), Łukasz Burnicki (s31052)

Przygotowanie środowiska (Python 3.10 lub nowszy):
    1. python -m venv .venv
    2. .venv\\Scripts\\python.exe -m pip install -r requirements.txt
    3. .venv\\Scripts\\python.exe main.py

Model jest edukacyjny i nie steruje prawdziwą baterią. Pełny opis zawierają
README.md i DOKUMENTACJA_KODU.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import time

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


SPRAWNOSC_LADOWANIA = 0.90
TEMPERATURA_OTOCZENIA = 25.0
TEMPERATURA_STOP = 45.0


class SterownikRozmyty:
    """Dobiera moc ładowania do poziomu baterii i jej nagrzewania.

    Attributes:
        _system (ctrl.ControlSystem): System sześciu reguł rozmytych.
    """

    def __init__(self) -> None:
        """Definiuje trzy wejścia, jedno wyjście i reguły szybkiego ładowania."""
        poziom = ctrl.Antecedent(np.arange(0, 101, 1), "poziom")
        temperatura = ctrl.Antecedent(np.arange(10, 51, 1), "temperatura")
        tempo = ctrl.Antecedent(np.linspace(-1, 1, 201), "tempo")
        moc = ctrl.Consequent(np.arange(0, 101, 1), "moc")

        # Do 80% poziom baterii nie ogranicza szybkiego ładowania.
        poziom["niedoladowana"] = fuzz.trapmf(poziom.universe, [0, 0, 80, 90])
        poziom["koncowka"] = fuzz.trapmf(poziom.universe, [80, 90, 100, 100])

        temperatura["normalna"] = fuzz.trapmf(
            temperatura.universe, [10, 10, 34, 38]
        )
        temperatura["ciepla"] = fuzz.trimf(temperatura.universe, [34, 40, 44])
        temperatura["goraca"] = fuzz.trapmf(
            temperatura.universe, [42, 45, 50, 50]
        )

        # Tempo <= 0 oznacza stygnięcie. Szybki wzrost uprzedza przegrzanie.
        tempo["stabilna"] = fuzz.trapmf(tempo.universe, [-1, -1, 0.2, 0.4])
        tempo["szybko_rosnie"] = fuzz.trapmf(tempo.universe, [0.2, 0.4, 1, 1])

        moc["wylacz"] = fuzz.trapmf(moc.universe, [0, 0, 0, 6])
        moc["mala"] = fuzz.trimf(moc.universe, [5, 25, 45])
        moc["srednia"] = fuzz.trimf(moc.universe, [35, 60, 85])
        moc["duza"] = fuzz.trapmf(moc.universe, [90, 97, 100, 100])

        reguly = [
            ctrl.Rule(temperatura["goraca"], moc["wylacz"]),
            ctrl.Rule(
                temperatura["normalna"] & tempo["stabilna"] & poziom["niedoladowana"],
                moc["duza"],
            ),
            ctrl.Rule(
                temperatura["normalna"] & tempo["stabilna"] & poziom["koncowka"],
                moc["srednia"],
            ),
            ctrl.Rule(temperatura["normalna"] & tempo["szybko_rosnie"], moc["srednia"]),
            ctrl.Rule(temperatura["ciepla"] & tempo["stabilna"], moc["srednia"]),
            ctrl.Rule(temperatura["ciepla"] & tempo["szybko_rosnie"], moc["mala"]),
        ]
        self._system = ctrl.ControlSystem(reguly)

    def oblicz_moc(self, poziom: float, temperatura: float, tempo: float) -> float:
        """Wyznacza moc, uwzględniając nagrzewanie i końcówkę ładowania.

        Parameters:
            poziom (float): Poziom baterii od 0 do 100%.
            temperatura (float): Temperatura baterii od 10 do 50°C.
            tempo (float): Wygładzone tempo zmiany temperatury od -1 do 1°C/min.

        Returns:
            float: Moc od 0 do 100%. Przy pełnej baterii lub co najmniej 45°C
                zwraca 0%. Wyniki od 95% są ustawiane na pełne 100% mocy.

        Raises:
            ValueError: Gdy którykolwiek argument wykracza poza zakres modelu.
        """
        zakresy = {
            "poziom": (poziom, 0, 100),
            "temperatura": (temperatura, 10, 50),
            "tempo": (tempo, -1, 1),
        }
        for nazwa, (wartosc, minimum, maksimum) in zakresy.items():
            if not minimum <= wartosc <= maksimum:
                raise ValueError(f"{nazwa} musi być w zakresie od {minimum} do {maksimum}.")

        # Jednoznaczne ograniczenia działają niezależnie od nakładania się reguł.
        if poziom >= 100 or temperatura >= TEMPERATURA_STOP:
            return 0.0

        symulacja = ctrl.ControlSystemSimulation(self._system)
        symulacja.input["poziom"] = poziom
        symulacja.input["temperatura"] = temperatura
        symulacja.input["tempo"] = tempo
        symulacja.compute()
        wynik = float(symulacja.output["moc"])
        if wynik < 3:
            return 0.0
        return 100.0 if wynik >= 95 else wynik


@dataclass
class SymulacjaBaterii:
    """Symuluje ładowanie do pełna na podstawie bilansu energii.

    Attributes:
        poziom (float): Aktualny poziom baterii; domyślnie start od 20%.
        temperatura (float): Aktualna temperatura; domyślnie 28°C.
        tempo (float): Wygładzone tempo nagrzewania w °C/min.
        pojemnosc_wh (float): Pojemność przykładowej baterii, domyślnie 60 Wh.
        moc_ladowarki_w (float): Maksymalna moc ładowania, domyślnie 65 W.
        max_minut (int): Limit długości symulacji, domyślnie 180 minut.
        poziom_poczatkowy (float): Poziom baterii przed rozpoczęciem symulacji.
    """

    poziom: float = 20.0
    temperatura: float = 28.0
    tempo: float = 0.0
    pojemnosc_wh: float = 60.0
    moc_ladowarki_w: float = 65.0
    max_minut: int = 180
    sterownik: SterownikRozmyty = field(default_factory=SterownikRozmyty)
    minuta: int = field(default=0, init=False)
    poziom_poczatkowy: float = field(init=False)

    def __post_init__(self) -> None:
        """Sprawdza parametry modelu i zapamiętuje początkowy poziom baterii."""
        self.sterownik.oblicz_moc(self.poziom, self.temperatura, self.tempo)
        if not np.isfinite(self.pojemnosc_wh) or self.pojemnosc_wh <= 0:
            raise ValueError("Pojemność baterii musi być dodatnią, skończoną liczbą.")
        if not np.isfinite(self.moc_ladowarki_w) or self.moc_ladowarki_w <= 0:
            raise ValueError("Moc ładowarki musi być dodatnią, skończoną liczbą.")
        if not isinstance(self.max_minut, int) or self.max_minut < 1:
            raise ValueError("Limit minut musi być dodatnią liczbą całkowitą.")
        self.poziom_poczatkowy = self.poziom

    def zakonczona(self) -> bool:
        """Sprawdza warunek końca ładowania.

        Returns:
            bool: True po osiągnięciu 100% baterii albo limitu minut.
        """
        return self.poziom >= 100 or self.minuta >= self.max_minut

    def krok(self) -> float:
        """Oblicza moc i symuluje jedną minutę ładowania.

        Energia dostarczona w minutę to moc razy sprawność podzielona przez 60.
        Temperatura zależy od ładowania i chłodzenia do temperatury otoczenia.

        Returns:
            float: Średnia moc użyta w tej minucie, w procentach.
                Po zakończeniu symulacji zwraca 0 bez przesuwania czasu.
        """
        if self.zakonczona():
            return 0.0
        moc = self.sterownik.oblicz_moc(self.poziom, self.temperatura, self.tempo)
        pelny_przyrost = self.moc_ladowarki_w * SPRAWNOSC_LADOWANIA / 60 / self.pojemnosc_wh * 100
        przyrost = min(100 - self.poziom, pelny_przyrost * moc / 100)
        # Ostatnia minuta dostarcza tylko energię potrzebną do uzyskania 100%.
        moc = przyrost / pelny_przyrost * 100
        self.poziom = min(100.0, self.poziom + przyrost)

        poprzednia_temperatura = self.temperatura
        ogrzewanie = 0.35 * (moc / 100) ** 2
        chlodzenie = 0.012 * (self.temperatura - TEMPERATURA_OTOCZENIA)
        self.temperatura = min(50.0, max(10.0, self.temperatura + ogrzewanie - chlodzenie))
        zmiana = self.temperatura - poprzednia_temperatura
        # Wygładzenie ogranicza gwałtowne przełączanie mocy między minutami.
        self.tempo = 0.7 * self.tempo + 0.3 * zmiana
        self.minuta += 1
        return moc


def wypisz_podsumowanie(symulator: SymulacjaBaterii) -> None:
    """Wyświetla wynik zakończonej lub przerwanej demonstracji.

    Parameters:
        symulator (SymulacjaBaterii): Obiekt z aktualnym stanem baterii.
    """
    start = symulator.poziom_poczatkowy
    print(
        f"Wynik: {start:.0f}% -> {symulator.poziom:.1f}% w {symulator.minuta} min modelu; "
        f"temperatura {symulator.temperatura:.1f}°C."
    )
    if symulator.poziom >= 100:
        print("Bateria pełna — ładowanie zakończone.")
    if symulator.poziom < 100 and symulator.minuta >= symulator.max_minut:
        print("Osiągnięto limit czasu symulacji przed pełnym naładowaniem.")


def uruchom_na_zywo(symulator: SymulacjaBaterii) -> None:
    """Pokazuje każdy krok, kończąc po naładowaniu albo przerwaniu przez Ctrl+C.

    Parameters:
        symulator (SymulacjaBaterii): Model używany w demonstracji.
    """
    print(
        f"Start: bateria {symulator.poziom:.0f}%, {symulator.temperatura:.1f}°C; "
        f"{symulator.pojemnosc_wh:.0f} Wh / {symulator.moc_ladowarki_w:.0f} W.\n"
        "1 krok = 1 minuta modelu; przerwa 0,1 s. Ctrl+C przerywa demonstrację.",
        flush=True,
    )
    try:
        while not symulator.zakonczona():
            moc = symulator.krok()
            print(
                f"{symulator.minuta:3d} min | bateria {symulator.poziom:5.1f}% | "
                f"temperatura {symulator.temperatura:4.1f}°C | "
                f"wzrost {symulator.tempo:+.2f}°C/min | moc {moc:5.1f}%",
                flush=True,
            )
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nPrzerwano symulację.")
    wypisz_podsumowanie(symulator)


def main() -> None:
    """Odczytuje parametry początkowe i uruchamia symulację w terminalu."""
    parser = argparse.ArgumentParser(description="Szybkie ładowanie z logiką rozmytą.")
    parser.add_argument("--poziom", type=float, default=20, help="początkowy poziom baterii (0–100)")
    parser.add_argument("--temperatura", type=float, default=28, help="początkowa temperatura (10–50°C)")
    args = parser.parse_args()
    try:
        symulator = SymulacjaBaterii(poziom=args.poziom, temperatura=args.temperatura)
    except ValueError as blad:
        parser.error(str(blad))
    uruchom_na_zywo(symulator)


if __name__ == "__main__":
    main()
