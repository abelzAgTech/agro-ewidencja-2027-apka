import math
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. KONFIGURACJA STRONY
# ==========================================
st.set_page_config(
    page_title="AgroCompliance 2027 | Asystent Oprysków",
    page_icon="🚜",
    layout="wide",
)


# ==========================================
# 2. FUNKCJE POMOCNICZE I FIZYCZNE
# ==========================================
def safe_float(value, default=0.0):
    """Bezpiecznie konwertuje tekst z API IMGW na liczbę zmiennoprzecinkową."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_wet_bulb_stull(temp_c: float, rh: float) -> float:
    """Wylicza temperaturę termometru mokrego (Tw) ze wzoru empirycznego Stulla (2011).

    temp_c: Temperatura powietrza w °C
    rh: Wilgotność względna w % (5 - 99%)
    """
    # Zabezpieczenie przed skrajnymi wartościami wilgotności
    rh = max(5.0, min(99.0, rh))

    term1 = temp_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
    term2 = math.atan(temp_c + rh)
    term3 = math.atan(rh - 1.676331)
    term4 = 0.00391838 * (rh**1.5) * math.atan(0.023101 * rh)

    tw = term1 + term2 - term3 + term4 - 4.686035
    return round(tw, 2)


def calculate_delta_t(temp_c: float, rh: float) -> float:
    """Wylicza wskaźnik Delta-T (tempo parowania kropli oprysku)."""
    tw = calculate_wet_bulb_stull(temp_c, rh)
    return round(temp_c - tw, 1)


@st.cache_data(ttl=1800)
def fetch_imgw_synop_data():
    """Pobiera dane ze wszystkich stacji synoptycznych IMGW-PIB.

    Dane są buforowane w pamięci podręcznej przez 30 minut (1800 sekund).
    """
    url = "https://danepubliczne.imgw.pl/api/data/synop"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


# ==========================================
# 3. NAGŁÓWEK APLIKACJI
# ==========================================
st.title("🚜 AgroCompliance 2027: Asystent Oprysków i Ewidencji ŚOR")
st.markdown(
    "**Wersja rozwojowa v0.2** | Moduł 1: Radar Okna Opryskowego na żywo (IMGW-PIB + Fizykochemia Delta-T) "
    "zgodny z wymogami kontroli PIORiN oraz rozporządzeniem KE (UE) 2023/564."
)
st.divider()

# ==========================================
# 4. POBRANIE DANYCH Z IMGW I WYBÓR STACJI
# ==========================================
data, error = fetch_imgw_synop_data()

col_select, col_manual = st.columns([1, 1])

with col_select:
    st.subheader("📡 1. Dane ze stacji meteorologicznej (IMGW)")

    if error or not data:
        st.warning(
            f"Nie udało się pobrać danych z IMGW ({error}). Użyj ręcznych suwaków obok."
        )
        station_dict = {}
        selected_station_name = "Tryb ręczny"
        default_temp, default_rh, default_wind = 18.0, 60.0, 2.5
        measurement_time = "Brak danych z API"
    else:
        # Tworzymy słownik stacji posortowany alfabetycznie
        station_dict = {item["stacja"]: item for item in data if "stacja" in item}
        station_names = sorted(list(station_dict.keys()))

        # Domyślnie ustawiamy Rzeszów, jeśli jest na liście
        default_index = (
            station_names.index("Rzeszów") if "Rzeszów" in station_names else 0
        )

        selected_station_name = st.selectbox(
            "Wybierz najbliższą stację synoptyczną IMGW-PIB:",
            options=station_names,
            index=default_index,
        )

        station_data = station_dict[selected_station_name]
        default_temp = safe_float(station_data.get("temperatura"), 15.0)
        default_rh = safe_float(station_data.get("wilgotnosc_wzgledna"), 65.0)
        default_wind = safe_float(station_data.get("predkosc_wiatru"), 2.0)
        measurement_date = station_data.get("data_pomiaru", "-")
        measurement_hour = station_data.get("godzina_pomiaru", "-")
        measurement_time = f"{measurement_date}, godz. {measurement_hour}:00"

        st.caption(
            f"📅 Ostatni oficjalny pomiar na stacji **{selected_station_name}**: {measurement_time}"
        )

with col_manual:
    st.subheader("🎛️ 2. Korekta polowa (Symulacja na działce)")
    st.caption(
        "Jeśli masz własny wiatromierz/termometr na polu, możesz skorygować odczyty ze stacji:"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        temp_c = st.number_input(
            "Temperatura (°C)",
            min_value=-10.0,
            max_value=45.0,
            value=default_temp,
            step=0.5,
        )
    with c2:
        rh = st.number_input(
            "Wilgotność (%)",
            min_value=5.0,
            max_value=100.0,
            value=default_rh,
            step=1.0,
        )
    with c3:
        wind_ms = st.number_input(
            "Wiatr (m/s)",
            min_value=0.0,
            max_value=25.0,
            value=default_wind,
            step=0.5,
        )

# ==========================================
# 5. OBLICZENIA I SYGNALIZATOR OKNA OPRYSKOWEGO
# ==========================================
delta_t = calculate_delta_t(temp_c, rh)
wind_kmh = round(wind_ms * 3.6, 1)

st.divider()
st.subheader("🚦 3. Werdykt: Czy można wjeżdżać z opryskiwaczem?")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        label="Wskaźnik Delta-T (Parowanie)",
        value=f"{delta_t} °C",
        delta="Optimum: 2.0 - 8.0 °C",
        delta_color="normal" if 2.0 <= delta_t <= 8.0 else "inverse",
    )

with m2:
    st.metric(
        label="Prędkość wiatru",
        value=f"{wind_ms} m/s ({wind_kmh} km/h)",
        delta="Limit prawny: max 4.0 m/s",
        delta_color="normal" if wind_ms <= 4.0 else "inverse",
    )

with m3:
    st.metric(
        label="Temperatura powietrza",
        value=f"{temp_c} °C",
        delta="Optimum: 10 - 25 °C",
        delta_color="normal" if 10.0 <= temp_c <= 25.0 else "off",
    )

with m4:
    st.metric(
        label="Wilgotność względna",
        value=f"{rh} %",
        delta="Optimum: > 50%",
        delta_color="normal" if rh >= 50.0 else "off",
    )

# Logika decyzyjna (Prawo + Agronomia)
reasons_stop = []
reasons_warn = []

# 1. Weryfikacja wiatru (Wymóg prawny)
if wind_ms > 4.0:
    reasons_stop.append(
        f"❌ **PRZEKROCZONY LIMIT WIATRU ({wind_ms} m/s > 4.0 m/s):** Zgodnie z polskim prawem wykonywanie zabiegu jest zabronione (wysokie ryzyko znoszenia cieczy i mandatu PIORiN)."
    )
elif wind_ms > 3.0:
    reasons_warn.append(
        f"⚠️ **Podwyższony wiatr ({wind_ms} m/s):** Zabieg legalny, ale zalecane użycie rozpylaczy eżektorowych (antydryfowych)."
    )

# 2. Weryfikacja Delta-T (Fizyka kropli)
if delta_t > 10.0:
    reasons_stop.append(
        f"❌ **KRYTYCZNE DELTA-T ({delta_t} °C > 10 °C):** Ekstremalnie szybkie odparowywanie kropli w locie! Ryzyko poparzenia roślin i zerowej skuteczności zabiegu."
    )
elif delta_t > 8.0:
    reasons_warn.append(
        f"⚠️ **Wysokie Delta-T ({delta_t} °C):** Krople parują zbyt szybko. Zwiększ wydatek wody (l/ha), użyj grubszej kropli lub dodaj adiuwant olejowy/antywaporacyjny."
    )
elif delta_t < 2.0:
    reasons_warn.append(
        f"⚠️ **Zbyt niskie Delta-T ({delta_t} °C < 2 °C):** Powietrze nasycone parą wodną. Krople nie będą wysychać i mogą spływać z liści (ryzyko zmycia)."
    )

# 3. Weryfikacja temperatury
if temp_c > 25.0:
    reasons_warn.append(
        f"⚠️ **Wysoka temperatura ({temp_c} °C):** Ryzyko fitotoksyczności (szczególnie dla herbicydów i mieszanin z mocznikiem/siarczanem magnezu)."
    )
elif temp_c < 5.0:
    reasons_warn.append(
        f"⚠️ **Niska temperatura ({temp_c} °C):** Większość środków systemicznych (poza wybranymi substancjami jesiennymi) działa bardzo wolno poniżej 8-10 °C."
    )

# Wyświetlenie werdyktu
if reasons_stop:
    st.error("### 🛑 ZAKAZ OPRYSKU – Warunki niedopuszczalne!")
    for r in reasons_stop:
        st.markdown(r)
    for w in reasons_warn:
        st.markdown(w)
elif reasons_warn:
    st.warning("### ⚠️ OPRYSK WARUNKOWY – Zachowaj ostrożność!")
    for w in reasons_warn:
        st.markdown(w)
else:
    st.success(
        "### ✅ ZIELONE ŚWIATŁO – Idealne okno pogodowe na zabieg! (Delta-T oraz wiatr w pełnej normie)"
    )

# ==========================================
# 6. ZAPOWIEDŹ KOLEJNYCH MODUŁÓW (PODGLĄD EWIDENCJI 2027)
# ==========================================
st.divider()
with st.expander("📋 Podgląd: Struktura Elektronicznej Ewidencji Zabiegów UE 2023/564 (Wkrótce w v0.3 - v0.5)"):
    st.info(
        "Od 1 stycznia 2027 r. każdy profesjonalny użytkownik ŚOR ma obowiązek prowadzić ewidencję w formacie elektronicznym obejmującym poniższe kolumny. W kolejnych etapach ten formularz będzie wypełniany automatycznie z bazy MRiRW oraz GUGiK."
    )
    sample_df = pd.DataFrame(
        [
            {
                "1. Data i godzina": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "2. Identyfikator działki (GUGiK)": "181004_2.0005.214/3 (Wola Dalsza)",
                "3. Uprawa i kod EPPO": "Pszenica ozima (TRZAW)",
                "4. Faza BBCH": "BBCH 31 (1. kolanko)",
                "5. Powierzchnia (ha)": 4.50,
                "6. Pełna nazwa ŚOR": "Mospilan 20 SP",
                "7. Nr zezwolenia MRiRW": "R-367/2014d",
                "8. Dawka": "0.12 kg/ha",
                "9. Przyczyna zabiegu (Agrofag)": "Skrzypionki (LEMAOR)",
                "10. Warunki pogodowe (Auto-IMGW)": f"T: {temp_c}°C, RH: {rh}%, Wiatr: {wind_ms} m/s, ΔT: {delta_t}°C",
            }
        ]
    )
    st.dataframe(sample_df, use_container_width=True, hide_index=True)
