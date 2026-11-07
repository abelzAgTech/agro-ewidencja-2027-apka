# 🚜 AgroCompliance 2027 – Asystent Okna Opryskowego i Ewidencji ŚOR (UE 2023/564)

Aplikacja webowa wspierająca rolników oraz doradców agrotechnicznych w precyzyjnym planowaniu zabiegów ochrony roślin oraz automatyzacji ustawowej ewidencji zabiegów wchodzącej w życie **1 stycznia 2027 roku** (zgodnie z Rozporządzeniem Wykonawczym Komisji UE 2023/564).

## 🎯 Problem biznesowy i regulacyjny
Od 2026/2027 roku rolnicy w całej Unii Europejskiej mierzą się z zaostrzonymi wymogami prowadzenia dokumentacji ŚOR (obowiązek wpisywania kodów upraw **EPPO**, faz rozwojowych **BBCH**, dokładnych numerów zezwoleń **MRiRW** oraz rejestrowania warunków atmosferycznych podczas zabiegu). Jednocześnie błędy w doborze okna pogodowego (zbyt wysokie tempo parowania kropli **Delta-T** lub przekroczenie dopuszczalnej prędkości wiatru **4 m/s**) generują straty finansowe i ryzyko mandatów podczas kontroli **PIORiN**.

## 🚀 Zaimplementowane moduły (Changelog / Build in Public)

### ✅ Wersja v0.3 (Aktualna) – Słownik EPPO, Baza MRiRW i Kalkulator Tank-Mix
* **Słownik kodów unijnych EPPO i faz BBCH:** Automatyczne mapowanie nazw upraw na 5-literowe kody EPPO (np. `TRZAW` dla pszenicy ozimej, `BRSNW` dla rzepaku) oraz dopasowanie klucza faz rozwojowych BBCH i agrofagów.
* **Hybrydowa baza ŚOR (MRiRW):** Wbudowany katalog środków ochrony roślin z oficjalnymi numerami zezwoleń `R-.../rok` oraz moduł importu pełnego rejestru `.xlsx` z portalu `dane.gov.pl`.
* **Kalkulator logistyki opryskiwacza (Tank-Mix):** Wyliczanie dawek na pełne zbiorniki oraz tzw. końcówkę pola wraz z automatycznym sortowaniem kolejności wsypu/wlewu według formulacji chemicznej (`Kondycjoner -> WG/SP/WP -> CS/SC/SE -> SL -> EW/EC -> Nawozy dolistne`).
* **Generator rekordów UE 2023/564:** Automatyczne rozbijanie mieszanin zbiornikowych na pojedyncze wiersze ewidencyjne połączone z odczytem pogodowym IMGW oraz eksportem do pliku CSV/Excel.

### ✅ Wersja v0.2 – Radar Okna Opryskowego na Żywo
* **Integracja z otwartym API IMGW-PIB (`danepubliczne.imgw.pl`):** Automatyczne pobieranie bieżących odczytów ze stacji synoptycznych w całej Polsce.
* **Silnik fizykochemii kropli (Delta-T):** Wyliczanie temperatury termometru mokrego ze wzoru empirycznego **Stulla (2011)** oraz walidacja limitu prędkości wiatru (4.0 m/s).

### 🛠️ Roadmapa rozwoju (Kolejne etapy)
* **[Wersja v0.4]** Integracja z usługą **GUGiK ULDK** (automatyczne pobieranie identyfikatorów TERYT i dokładnej powierzchni działek ewidencyjnych z serwera geodezyjnego).
* **[Wersja v0.5]** Wielopole, pamięć historii zabiegów z całego sezonu oraz eksport sformatowanego raportu `.xlsx` / `.pdf` na kontrolę PIORiN.
* **[Wersja v0.6]** Asystent głosowy/tekstowy AI (automatyczne wypełnianie ewidencji z notatki głosowej rolnika).
