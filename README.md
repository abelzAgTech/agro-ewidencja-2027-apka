# 🚜 AgroCompliance 2027 – Asystent Okna Opryskowego i Ewidencji ŚOR (UE 2023/564)

Aplikacja webowa wspierająca rolników oraz doradców agrotechnicznych w precyzyjnym planowaniu zabiegów ochrony roślin oraz automatyzacji ustawowej ewidencji zabiegów wchodzącej w życie **1 stycznia 2027 roku** (zgodnie z Rozporządzeniem Wykonawczym Komisji UE 2023/564).

## 🎯 Problem biznesowy i regulacyjny
Od 2026/2027 roku rolnicy w całej Unii Europejskiej mierzą się z zaostrzonymi wymogami prowadzenia dokumentacji ŚOR (obowiązek wpisywania kodów upraw **EPPO**, faz rozwojowych **BBCH**, dokładnych numerów zezwoleń **MRiRW** oraz rejestrowania warunków atmosferycznych podczas zabiegu). Jednocześnie błędy w doborze okna pogodowego (zbyt wysokie tempo parowania kropli **Delta-T** lub przekroczenie dopuszczalnej prędkości wiatru **4 m/s**) generują straty finansowe i ryzyko mandatów podczas kontroli **PIORiN**.

## 🚀 Zaimplementowane moduły (Changelog / Build in Public)

### ✅ Wersja v0.4 (Aktualna) – Geolokalizacja GUGiK ULDK i Algorytm Powierzchni Gaussa
* **Integracja z API GUGiK ULDK (`uldk.gugik.gov.pl`):** Wyszukiwanie działek ewidencyjnych po nazwie obrębu i numerze (np. `Wola Dalsza 214`) lub po współrzędnych GPS (`EPSG:4326` -> `EPSG:2180`) wraz z pobraniem pełnego identyfikatora katastralnego **TERYT**.
* **Geodezyjny kalkulator powierzchni (Wzór Gaussa / *Shoelace Formula*):** Automatyczne parsowanie geometrii WKT (`POLYGON`) w państwowym układzie metrycznym PUWG 1992 (`EPSG:2180`) i wyliczanie dokładnej powierzchni działki w hektarach bez użycia zewnętrznych bibliotek GIS.
* **Wielopolowy Dziennik Ewidencji (`Session State`):** Możliwość zapisywania kolejnych zabiegów z różnych działek do wspólnego rejestru gospodarstwa i zbiorczego eksportu.

### ✅ Wersja v0.3 – Słownik EPPO, Baza MRiRW i Kalkulator Tank-Mix
* **Słownik kodów unijnych EPPO i faz BBCH:** Automatyczne mapowanie nazw upraw na 5-literowe kody EPPO (`TRZAW`, `BRSNW`, `ZEAMX` itd.) oraz dopasowanie faz BBCH i agrofagów.
* **Rozszerzona baza ŚOR (MRiRW):** Katalog popularnych środków ochrony roślin z oficjalnymi numerami zezwoleń `R-.../rok` oraz moduł importu pełnego rejestru `.xlsx` z `dane.gov.pl`.
* **Kalkulator logistyki opryskiwacza (Tank-Mix):** Wyliczanie dawek na pełne zbiorniki i końcówkę pola wraz z sortowaniem kolejności mieszania wg formulacji (`Kondycjoner -> WG/SP -> CS/SC/SE/OD -> SL -> EW/EC -> Nawozy`).

### ✅ Wersja v0.2 – Radar Okna Opryskowego na Żywo
* **Integracja z otwartym API IMGW-PIB (`danepubliczne.imgw.pl`):** Automatyczne pobieranie bieżących odczytów ze stacji synoptycznych.
* **Silnik fizykochemii kropli (Delta-T):** Wyliczanie temperatury termometru mokrego ze wzoru empirycznego **Stulla (2011)** oraz walidacja limitu prędkości wiatru (4.0 m/s).

### 🛠️ Roadmapa rozwoju (Kolejne etapy)
* **[Wersja v0.5]** Wielopole, pamięć historii zabiegów z całego sezonu oraz eksport sformatowanego raportu `.xlsx` / `.pdf` na kontrolę PIORiN.
* **[Wersja v0.6]** Asystent głosowy/tekstowy AI (automatyczne wypełnianie ewidencji z notatki głosowej rolnika).
