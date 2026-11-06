# 🚜 AgroCompliance 2027 – Asystent Okna Opryskowego i Ewidencji ŚOR (UE 2023/564)

Aplikacja webowa wspierająca rolników oraz doradców agrotechnicznych w precyzyjnym planowaniu zabiegów ochrony roślin oraz automatyzacji ustawowej ewidencji zabiegów wchodzącej w życie **1 stycznia 2027 roku** (zgodnie z Rozporządzeniem Wykonawczym Komisji UE 2023/564).

## 🎯 Problem biznesowy i regulacyjny
Od 2026/2027 roku rolnicy w całej Unii Europejskiej mierzą się z zaostrzonymi wymogami prowadzenia dokumentacji ŚOR (obowiązek wpisywania kodów upraw **EPPO**, faz rozwojowych **BBCH**, dokładnych numerów zezwoleń **MRiRW** oraz rejestrowania warunków atmosferycznych podczas zabiegu). Jednocześnie błędy w doborze okna pogodowego (zbyt wysokie tempo parowania kropli **Delta-T** lub przekroczenie dopuszczalnej prędkości wiatru **4 m/s**) generują straty finansowe i ryzyko mandatów podczas kontroli **PIORiN**.

## 🚀 Zaimplementowane moduły (Changelog / Build in Public)

### ✅ Wersja v0.2 (Aktualna) – Radar Okna Opryskowego na Żywo
* **Integracja z otwartym API IMGW-PIB (`danepubliczne.imgw.pl`):** Automatyczne pobieranie bieżących odczytów ze stacji synoptycznych w całej Polsce z buforowaniem zapytań (`@st.cache_data`).
* **Silnik fizykochemii kropli (Delta-T):** Wyliczanie temperatury termometru mokrego ze wzoru empirycznego **Stulla (2011)** oraz wskaźnika $\Delta T$ określającego tempo parowania cieczy roboczej.
* **Walidator prawno-agrotechniczny:** Automatyczna weryfikacja limitu wiatru ($< 4.0\text{ m/s}$) oraz ryzyka fitotoksyczności.

### 🛠️ Roadmapa rozwoju (Kolejne etapy)
* **[Wersja v0.3]** Integracja z oficjalną bazą Rejestru ŚOR **MRiRW** (`dane.gov.pl`) oraz słownikiem kodów **EPPO**.
* **[Wersja v0.4]** Integracja z usługą **GUGiK ULDK** (automatyczne pobieranie identyfikatorów TERYT i powierzchni działek ewidencyjnych).
* **[Wersja v0.5]** Kalkulator mieszanin zbiornikowych (*Tank-Mix*) oraz eksport 9-kolumnowej tabeli UE 2023/564 do plików `.xlsx` / `.pdf`.
* **[Wersja v0.6]** Asystent głosowy/tekstowy AI (automatyczne wypełnianie ewidencji z notatki głosowej rolnika).

## 💻 Stos technologiczny (Tech Stack)
* **Język:** Python 3.11+
* **Framework UI:** Streamlit
* **Przetwarzanie danych:** Pandas, Requests
* **Źródła danych (Open Data API):** IMGW-PIB, MRiRW, GUGiK ULDK, EPPO
