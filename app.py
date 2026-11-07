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
# 2. SŁOWNIKI DANYCH (EPPO, BBCH, BAZA ŚOR I FORMULACJE)
# ==========================================

# Słownik upraw, kodów EPPO, typowych faz BBCH oraz agrofagów (z kodami EPPO)
EPPO_CROPS_DB = {
    "Pszenica ozima": {
        "eppo_code": "TRZAW",
        "bbch_stages": [
            "BBCH 10-19 (Wschody i rozwój liści - jesień)",
            "BBCH 21-29 (Krzewienie)",
            "BBCH 30-31 (Początek strzelania w źdźbło / 1. kolanko)",
            "BBCH 32-37 (2. kolanko - liść flagowy)",
            "BBCH 39 (Całkowicie rozwinięty liść flagowy - T2)",
            "BBCH 51-59 (Kłoszenie)",
            "BBCH 61-69 (Kwitnienie - zabieg T3 na kłos)",
        ],
        "pests": [
            "Chwasty dwuliścienne (TTTDD)",
            "Miotła zbożowa (APESV)",
            "Skrzypionki zbożowe (LEMAOR)",
            "Mszyce zbożowe (SITAVE)",
            "Septorioza paskowana liści (ZIMYTR)",
            "Mączniak prawdziwy zbóż (BLUMGR)",
            "Fuzarioza kłosów (FUSASP)",
        ],
    },
    "Rzepak ozimy": {
        "eppo_code": "BRSNW",
        "bbch_stages": [
            "BBCH 00-09 (Przedwschodowo - doglebowo)",
            "BBCH 12-18 (Rozwój rozety liściowej - jesień)",
            "BBCH 30-39 (Wydłużanie pędu głównego - wiosna)",
            "BBCH 50-59 (Rozwój pąków kwiatowych - zielony pąk)",
            "BBCH 60-65 (Kwitnienie - opadanie pierwszych płatków)",
        ],
        "pests": [
            "Chwasty jednoliścienne i dwuliścienne (TTTMM)",
            "Chowacz brukwiaczek (CEUTNA)",
            "Chowacz czterozębny (CEUTPA)",
            "Słodyszek rzepakowy (MELIAE)",
            "Chowacz podobnik i pryszczarek (CEUTAS)",
            "Zgnilizna twardzikowa (SCLESC)",
            "Sucha zgnilizna kapustnych (LEPTMA)",
        ],
    },
    "Kukurydza": {
        "eppo_code": "ZEAMX",
        "bbch_stages": [
            "BBCH 00-09 (Przedwschodowo)",
            "BBCH 12-16 (Faza 2-6 liści właściwych)",
            "BBCH 17-19 (Faza 7-9 liści)",
            "BBCH 30-39 (Wydłużanie źdźbła)",
            "BBCH 51-65 (Wyrzucanie wiechy i kwitnienie)",
        ],
        "pests": [
            "Chwastnica jednostronna i dwuliścienne (ECHCG)",
            "Omacnica prosowianka (OSTRNU)",
            "Zachodnia stonka kukurydziana (DIABVI)",
            "Ploniarka zbożówka (OSCIFF)",
        ],
    },
    "Jęczmień jary / ozimy": {
        "eppo_code": "HORVX",
        "bbch_stages": [
            "BBCH 21-29 (Krzewienie)",
            "BBCH 30-32 (1-2 kolanko)",
            "BBCH 37-39 (Liść podflagowy i flagowy)",
            "BBCH 51-59 (Kłoszenie)",
        ],
        "pests": [
            "Chwasty dwuliścienne (TTTDD)",
            "Plamistość siatkowa jęczmienia (PYRNTE)",
            "Rynchosporioza zbóż (RHYNSE)",
            "Skrzypionki zbożowe (LEMAOR)",
        ],
    },
    "Ziemniak": {
        "eppo_code": "SOLTU",
        "bbch_stages": [
            "BBCH 00-09 (Przedwschodowo po obredleniu)",
            "BBCH 11-19 (Rozwój liści)",
            "BBCH 31-39 (Zakrywanie międzyrzędzi)",
            "BBCH 51-69 (Pąkowanie i kwitnienie)",
        ],
        "pests": [
            "Zaraza ziemniaka (PHYTIN)",
            "Alternarioza ziemniaka (ALTESO)",
            "Stonka ziemniaczana (LEPTDE)",
            "Chwasty jedno- i dwuliścienne (TTTMM)",
        ],
    },
    "Pomidor / Papryka (Grunt i osłony)": {
        "eppo_code": "LYPES",
        "bbch_stages": [
            "BBCH 12-19 (Rozwój liści po wysadzeniu)",
            "BBCH 51-69 (Kwitnienie kolejnych gron)",
            "BBCH 71-89 (Rozwój i dojrzewanie owoców)",
        ],
        "pests": [
            "Zaraza ziemniaka na pomidorze (PHYTIN)",
            "Szara pleśń (BOTRCI)",
            "Mszyce i mączliki (TRIAVA)",
        ],
    },
}

# Reguły kolejności mieszania w zbiorniku opryskiwacza (im mniejsza liczba, tym wcześniej wlewamy/wsypujemy)
FORMULATION_MIXING_ORDER = {
    "KOND": (1, "1. Kondycjoner wody / Bufor pH (przed wszystkimi środkami)"),
    "WG": (2, "2. Granulaty do sporządzania zawiesiny (WG / SG)"),
    "SP": (2, "2. Proszki rozpuszczalne w wodzie (SP)"),
    "WP": (2, "2. Proszki do sporządzania zawiesiny (WP)"),
    "CS": (3, "3. Zawiesiny kapsuł i koncentraty zawiesinowe (CS / SC)"),
    "SC": (3, "3. Koncentraty stężonych zawiesin (SC)"),
    "SE": (3, "3. Zawiesino-emulsje (SE)"),
    "SL": (4, "4. Koncentraty rozpuszczalne w wodzie (SL)"),
    "EW": (5, "5. Emulsje olej w wodzie (EW)"),
    "EC": (5, "5. Koncentraty do sporządzania emulsji wodnej (EC / OD)"),
    "NAW": (
        6,
        "6. Nawozy dolistne i mikroelementy (po rozpuszczeniu lub zgodnie z etykietą)",
    ),
    "ADI": (7, "7. Adiuwanty olejowe i zwilżacze (na sam koniec)"),
}

# Wbudowana baza popularnych Środków Ochrony Roślin (z oficjalnymi numerami MRiRW)
DEFAULT_SOR_DB = [
    {
        "nazwa": "Chwastox Trio 540 SL",
        "nr_zezwolenia": "R-110/2014",
        "kategoria": "Herbicyd",
        "substancja": "mekoprop-P + MCPA + dikamba",
        "formulacja": "SL",
        "dawka_domyslna": 2.0,
        "jednostka": "l/ha",
    },
    {
        "nazwa": "Mospilan 20 SP",
        "nr_zezwolenia": "R-367/2014d",
        "kategoria": "Insektycyd",
        "substancja": "acetamipryd (20%)",
        "formulacja": "SP",
        "dawka_domyslna": 0.12,
        "jednostka": "kg/ha",
    },
    {
        "nazwa": "Stomp Aqua 455 CS",
        "nr_zezwolenia": "R-133/2013",
        "kategoria": "Herbicyd",
        "substancja": "pendimetalina (455 g/l)",
        "formulacja": "CS",
        "dawka_domyslna": 2.5,
        "jednostka": "l/ha",
    },
    {
        "nazwa": "Axial 50 EC",
        "nr_zezwolenia": "R-108/2019",
        "kategoria": "Herbicyd",
        "substancja": "pinoksaden (50 g/l)",
        "formulacja": "EC",
        "dawka_domyslna": 0.9,
        "jednostka": "l/ha",
    },
    {
        "nazwa": "Mustang Forte 195 SE",
        "nr_zezwolenia": "R-122/2011",
        "kategoria": "Herbicyd",
        "substancja": "florasulam + aminopyralid + 2,4-D",
        "formulacja": "SE",
        "dawka_domyslna": 1.0,
        "jednostka": "l/ha",
    },
    {
        "nazwa": "Tebu 250 EW",
        "nr_zezwolenia": "R-71/2014",
        "kategoria": "Fungicyd",
        "substancja": "tebukonazol (250 g/l)",
        "formulacja": "EW",
        "dawka_domyslna": 1.0,
        "jednostka": "l/ha",
    },
    {
        "nazwa": "Inazuma 130 WG",
        "nr_zezwolenia": "R-91/2015",
        "kategoria": "Insektycyd",
        "substancja": "acetamipryd + lambda-cyhalotryna",
        "formulacja": "WG",
        "dawka_domyslna": 0.20,
        "jednostka": "kg/ha",
    },
    {
        "nazwa": "Azoksystrobina 250 SC (Amistar 250 SC)",
        "nr_zezwolenia": "R-98/2011",
        "kategoria": "Fungicyd",
        "substancja": "azoksystrobina (250 g/l)",
        "formulacja": "SC",
        "dawka_domyslna": 0.8,
        "jednostka": "l/ha",
    },
]

# Baza dodatków zbiornikowych (Nawozy dolistne i kondycjonery - nie wchodzą do rejestru PIORiN, ale wchodzą do zbiornika)
FOLIAR_ADDITIVES_DB = {
    "Mocznik (46% N - dokarmianie dolistne)": {
        "formulacja": "NAW",
        "dawka_domyslna": 12.0,
        "jednostka": "kg/ha",
    },
    "Siarczan magnezu siedmiowodny (16% MgO + 32% SO3)": {
        "formulacja": "NAW",
        "dawka_domyslna": 5.0,
        "jednostka": "kg/ha",
    },
    "Nawóz wieloskładnikowy NPK 20-20-20 + mikro": {
        "formulacja": "NAW",
        "dawka_domyslna": 3.0,
        "jednostka": "kg/ha",
    },
    "Siarczan amonu (Kondycjoner twardej wody / Bufor pH)": {
        "formulacja": "KOND",
        "dawka_domyslna": 0.5,
        "jednostka": "kg/ha",
    },
    "Adiuwant zmniejszający napięcie powierzchniowe / antydryfowy": {
        "formulacja": "ADI",
        "dawka_domyslna": 0.15,
        "jednostka": "l/ha",
    },
}


# ==========================================
# 3. FUNKCJE POMOCNICZE I FIZYCZNE
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
    """Wylicza temperaturę termometru mokrego (Tw) ze wzoru empirycznego Stulla (2011)."""
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
    """Pobiera dane ze wszystkich stacji synoptycznych IMGW-PIB (cache 30 min)."""
    url = "https://danepubliczne.imgw.pl/api/data/synop"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


# Inicjalizacja bazy ŚOR w pamięci sesji (pozwala dodawać własne środki w locie)
if "sor_db" not in st.session_state:
    st.session_state.sor_db = DEFAULT_SOR_DB.copy()


# ==========================================
# 4. NAGŁÓWEK APLIKACJI
# ==========================================
st.title("🚜 AgroCompliance 2027: Asystent Oprysków i Ewidencji ŚOR")
st.markdown(
    "**Wersja rozwojowa v0.3** | Moduł 1: Radar Pogodowy IMGW & Delta-T | "
    "Moduł 2: Słownik EPPO, Baza MRiRW i Kalkulator Zbiornika (Tank-Mix)"
)
st.divider()

# ==========================================
# 5. MODUŁ 1: RADAR OKNA OPRYSKOWEGO (IMGW + DELTA-T)
# ==========================================
st.header("📡 Moduł 1: Warunki Pogodowe i Fizykochemia Kropli (Delta-T)")

data, error = fetch_imgw_synop_data()
col_select, col_manual = st.columns([1, 1])

with col_select:
    st.subheader("1. Stacja meteorologiczna IMGW-PIB")
    if error or not data:
        st.warning(
            f"Nie udało się pobrać danych z IMGW ({error}). Użyj ręcznych suwaków obok."
        )
        selected_station_name = "Tryb ręczny"
        default_temp, default_rh, default_wind = 18.0, 60.0, 2.5
    else:
        station_dict = {item["stacja"]: item for item in data if "stacja" in item}
        station_names = sorted(list(station_dict.keys()))
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
        st.caption(
            f"📅 Ostatni oficjalny pomiar na stacji **{selected_station_name}**: {measurement_date}, godz. {measurement_hour}:00"
        )

with col_manual:
    st.subheader("2. Korekta polowa (Odczyt na działce)")
    st.caption(
        "W razie potrzeby skoryguj dane ze stacji własnym pomiarem z pola:"
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

delta_t = calculate_delta_t(temp_c, rh)
wind_kmh = round(wind_ms * 3.6, 1)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(
        "Wskaźnik Delta-T",
        f"{delta_t} °C",
        "Optimum: 2.0 - 8.0 °C",
        delta_color="normal" if 2.0 <= delta_t <= 8.0 else "inverse",
    )
with m2:
    st.metric(
        "Prędkość wiatru",
        f"{wind_ms} m/s ({wind_kmh} km/h)",
        "Max prawny: 4.0 m/s",
        delta_color="normal" if wind_ms <= 4.0 else "inverse",
    )
with m3:
    st.metric(
        "Temperatura",
        f"{temp_c} °C",
        "Optimum: 10 - 25 °C",
        delta_color="normal" if 10.0 <= temp_c <= 25.0 else "off",
    )
with m4:
    st.metric(
        "Wilgotność względna",
        f"{rh} %",
        "Optimum: powyżej 50%",
        delta_color="normal" if rh >= 50.0 else "off",
    )

reasons_stop, reasons_warn = [], []
if wind_ms > 4.0:
    reasons_stop.append(
        f"❌ **PRZEKROCZONY LIMIT WIATRU ({wind_ms} m/s):** Zabieg prawnie zabroniony (ryzyko znoszenia cieczy i mandatu PIORiN)."
    )
elif wind_ms > 3.0:
    reasons_warn.append(
        f"⚠️ **Podwyższony wiatr ({wind_ms} m/s):** Zalecane użycie rozpylaczy eżektorowych (antydryfowych)."
    )

if delta_t > 10.0:
    reasons_stop.append(
        f"❌ **KRYTYCZNE DELTA-T ({delta_t} °C):** Ekstremalnie szybkie odparowywanie kropli w locie! Ryzyko poparzenia roślin."
    )
elif delta_t > 8.0:
    reasons_warn.append(
        f"⚠️ **Wysokie Delta-T ({delta_t} °C):** Krople szybko parują. Zwiększ wydatek wody lub dodaj adiuwant."
    )
elif delta_t < 2.0:
    reasons_warn.append(
        f"⚠️ **Niskie Delta-T ({delta_t} °C):** Krople mogą spływać z liści (powietrze nasycone parą wodną)."
    )

if temp_c > 25.0:
    reasons_warn.append(
        f"⚠️ **Wysoka temperatura ({temp_c} °C):** Ryzyko fitotoksyczności (szczególnie z mocznikiem i herbicydami)."
    )

if reasons_stop:
    st.error("### 🛑 ZAKAZ OPRYSKU – Warunki niedopuszczalne!")
    for r in reasons_stop + reasons_warn:
        st.markdown(r)
elif reasons_warn:
    st.warning("### ⚠️ OPRYSK WARUNKOWY – Zachowaj ostrożność!")
    for w in reasons_warn:
        st.markdown(w)
else:
    st.success(
        "### ✅ ZIELONE ŚWIATŁO – Idealne okno pogodowe na zabieg!"
    )

st.divider()

# ==========================================
# 6. MODUŁ 2: SŁOWNIK EPPO, BAZA ŚOR I KALKULATOR ZBIORNIKA
# ==========================================
st.header("🧪 Moduł 2: Kreator Zabiegu (Słownik EPPO + Baza MRiRW + Tank-Mix)")

# Sekcja opcjonalnego dodania własnego ŚOR lub wgrania pliku z dane.gov.pl
with st.expander("➕ Nie widzisz swojego preparatu na liście? Dodaj środek z etykiety lub wgraj plik Excel z MRiRW"):
    tab_manual_sor, tab_excel_sor = st.tabs(
        ["Dopisz pojedynczy środek", "Wgraj oficjalny plik .xlsx z dane.gov.pl"]
    )

    with tab_manual_sor:
        mc1, mc2, mc3, mc4, mc5 = st.columns([2, 1.5, 1, 1, 1])
        with mc1:
            new_name = st.text_input(
                "Pełna nazwa handlowa ŚOR", placeholder="np. Puma Uniwersal 069 EW"
            )
        with mc2:
            new_perm = st.text_input(
                "Nr zezwolenia MRiRW", placeholder="np. R-121/2014"
            )
        with mc3:
            new_form = st.selectbox(
                "Formulacja", options=["SL", "EC", "EW", "SC", "CS", "SE", "WG", "SP", "WP"]
            )
        with mc4:
            new_dose = st.number_input(
                "Dawka domyślna", min_value=0.01, max_value=20.0, value=1.0, step=0.1
            )
        with mc5:
            new_unit = st.selectbox("Jednostka", options=["l/ha", "kg/ha"])

        if st.button("Dodaj środek do bazy sesji"):
            if new_name and new_perm:
                st.session_state.sor_db.append(
                    {
                        "nazwa": new_name,
                        "nr_zezwolenia": new_perm,
                        "kategoria": "ŚOR użytkownika",
                        "substancja": "Zgodnie z etykietą",
                        "formulacja": new_form,
                        "dawka_domyslna": new_dose,
                        "jednostka": new_unit,
                    }
                )
                st.success(f"Dodano **{new_name}** ({new_perm}) do listy wyboru!")
            else:
                st.warning("Podaj przynajmniej nazwę środka oraz numer zezwolenia.")

    with tab_excel_sor:
        st.caption(
            "Możesz pobrać aktualny plik `.xlsx` z Rejestrem ŚOR ze strony rządowej `dane.gov.pl` i przeciągnąć go tutaj:"
        )
        uploaded_file = st.file_uploader(
            "Wybierz plik Excel (.xlsx) lub CSV z rejestrem MRiRW",
            type=["xlsx", "csv"],
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_mrirw = pd.read_csv(uploaded_file)
                else:
                    df_mrirw = pd.read_excel(uploaded_file)
                st.success(
                    f"Wczytano plik rządowy! Liczba wierszy w rejestrze: {len(df_mrirw)}"
                )
                st.dataframe(df_mrirw.head(5), use_container_width=True)
            except Exception as e:
                st.error(f"Błąd podczas czytania pliku: {e}")

# Główny formularz pola, uprawy (EPPO) i opryskiwacza
col_field, col_sprayer = st.columns([1, 1])

with col_field:
    st.subheader("🌾 1. Działka, Uprawa (EPPO) i Faza BBCH")

    parcel_id = st.text_input(
        "Numer ewidencyjny działki / Nazwa pola (w Etapie 3 podepniemy GUGiK ULDK):",
        value="Działka 214/3 (Wola Dalsza)",
    )

    area_ha = st.number_input(
        "Powierzchnia zabiegu (ha):",
        min_value=0.10,
        max_value=500.0,
        value=12.50,
        step=0.50,
    )

    selected_crop = st.selectbox(
        "Wybierz uprawę (automatyczne mapowanie kodu EPPO):",
        options=list(EPPO_CROPS_DB.keys()),
    )

    crop_info = EPPO_CROPS_DB[selected_crop]
    eppo_crop_code = crop_info["eppo_code"]
    st.info(
        f"🇪🇺 Wymagany kod unijny EPPO dla wybranej uprawy: **`{eppo_crop_code}`** ({selected_crop})"
    )

    selected_bbch = st.selectbox(
        "Faza rozwojowa rośliny w skali BBCH:",
        options=crop_info["bbch_stages"],
    )

    selected_pest = st.selectbox(
        "Główna przyczyna zabiegu / zwalczany agrofag (z kodem EPPO):",
        options=crop_info["pests"],
    )

with col_sprayer:
    st.subheader("🚜 2. Parametry Opryskiwacza i Wybór Preparatów")

    sc1, sc2 = st.columns(2)
    with sc1:
        tank_capacity_l = st.number_input(
            "Pojemność zbiornika opryskiwacza (l):",
            min_value=100,
            max_value=10000,
            value=1200,
            step=100,
        )
    with sc2:
        water_rate_l_ha = st.number_input(
            "Wydatek cieczy roboczej (l wody / ha):",
            min_value=50,
            max_value=1000,
            value=200,
            step=10,
        )

    sor_names_map = {item["nazwa"]: item for item in st.session_state.sor_db}
    selected_sor_names = st.multiselect(
        "Wybierz Środki Ochrony Roślin do mieszaniny (trafią do ewidencji PIORiN):",
        options=list(sor_names_map.keys()),
        default=["Chwastox Trio 540 SL", "Mospilan 20 SP"],
    )

    selected_foliar_names = st.multiselect(
        "Opcjonalnie: Dodaj nawozy dolistne / kondycjonery wody do zbiornika:",
        options=list(FOLIAR_ADDITIVES_DB.keys()),
        default=["Siarczan magnezu siedmiowodny (16% MgO + 32% SO3)"],
    )

# Konfiguracja dokładnych dawek dla wybranych produktów
st.subheader("⚖️ 3. Dostosuj dawki na hektar i odbierz recepturę na zbiornik")

chosen_products_configured = []

if not selected_sor_names and not selected_foliar_names:
    st.warning("Wybierz przynajmniej jeden środek lub nawóz z listy powyżej, aby przeliczyć zbiornik.")
else:
    dose_cols = st.columns(min(4, max(1, len(selected_sor_names) + len(selected_foliar_names))))
    col_idx = 0

    # 1. Konfiguracja dawek ŚOR
    for sor_name in selected_sor_names:
        sor_item = sor_names_map[sor_name]
        with dose_cols[col_idx % len(dose_cols)]:
            user_dose = st.number_input(
                f"{sor_name} ({sor_item['jednostka']})",
                min_value=0.01,
                max_value=25.0,
                value=float(sor_item["dawka_domyslna"]),
                step=0.05,
                key=f"dose_sor_{sor_name}",
            )
            st.caption(
                f"Nr zezw.: `{sor_item['nr_zezwolenia']}` | Formulacja: **{sor_item['formulacja']}**"
            )
            chosen_products_configured.append(
                {
                    "typ": "ŚOR (Ewidencjonowany)",
                    "nazwa": sor_name,
                    "nr_zezwolenia": sor_item["nr_zezwolenia"],
                    "formulacja": sor_item["formulacja"],
                    "dawka_ha": user_dose,
                    "jednostka": sor_item["jednostka"],
                    "is_sor": True,
                }
            )
        col_idx += 1

    # 2. Konfiguracja dawek nawozów dolistnych / dodatków
    for fol_name in selected_foliar_names:
        fol_item = FOLIAR_ADDITIVES_DB[fol_name]
        with dose_cols[col_idx % len(dose_cols)]:
            user_dose = st.number_input(
                f"{fol_name} ({fol_item['jednostka']})",
                min_value=0.05,
                max_value=50.0,
                value=float(fol_item["dawka_domyslna"]),
                step=0.5,
                key=f"dose_fol_{fol_name}",
            )
            st.caption(f"Dodatek zbiornikowy | Typ: **{fol_item['formulacja']}**")
            chosen_products_configured.append(
                {
                    "typ": "Dodatek / Nawóz dolistny",
                    "nazwa": fol_name,
                    "nr_zezwolenia": "Nie dotyczy (Nawóz/Dodatek)",
                    "formulacja": fol_item["formulacja"],
                    "dawka_ha": user_dose,
                    "jednostka": fol_item["jednostka"],
                    "is_sor": False,
                }
            )
        col_idx += 1

    # ==========================================
    # OBLICZENIA ZBIORNIKA OPRYSKIWACZA (TANK-MIX)
    # ==========================================
    total_liquid_l = round(area_ha * water_rate_l_ha, 1)
    max_ha_per_tank = round(tank_capacity_l / water_rate_l_ha, 2)
    full_tanks_count = int(total_liquid_l // tank_capacity_l)
    remainder_liquid_l = round(total_liquid_l % tank_capacity_l, 1)
    remainder_ha = round(remainder_liquid_l / water_rate_l_ha, 2)

    st.markdown("#### 💧 Podsumowanie logistyki opryskiwacza:")
    tm1, tm2, tm3, tm4 = st.columns(4)
    with tm1:
        st.metric("Całkowita ilość cieczy", f"{total_liquid_l} l wody", f"Na {area_ha} ha")
    with tm2:
        st.metric(
            "Wydajność 1 pełnego zbiornika",
            f"{max_ha_per_tank} ha",
            f"Przy {water_rate_l_ha} l/ha",
        )
    with tm3:
        st.metric("Pełne zbiorniki", f"{full_tanks_count} szt.", f"Po {tank_capacity_l} l każdy")
    with tm4:
        if remainder_liquid_l > 0:
            st.metric(
                "Ostatni niepełny zbiornik (Końcówka)",
                f"{remainder_liquid_l} l wody",
                f"Pokryje pozostałe {remainder_ha} ha",
            )
        else:
            st.metric("Ostatni niepełny zbiornik", "Brak (0 l)", "Równy podział zbiorników")

    # Sortowanie produktów według prawidłowej kolejności wlewania do opryskiwacza
    chosen_products_configured.sort(
        key=lambda x: FORMULATION_MIXING_ORDER.get(x["formulacja"], (9, "Inne"))[0]
    )

    tank_table_rows = []
    for step_num, prod in enumerate(chosen_products_configured, start=1):
        unit_short = "l" if "l/" in prod["jednostka"] else "kg"
        total_need = round(prod["dawka_ha"] * area_ha, 2)
        per_full_tank = (
            round(prod["dawka_ha"] * max_ha_per_tank, 2)
            if full_tanks_count > 0
            else 0.0
        )
        per_remainder_tank = (
            round(prod["dawka_ha"] * remainder_ha, 2)
            if remainder_liquid_l > 0
            else 0.0
        )
        order_desc = FORMULATION_MIXING_ORDER.get(
            prod["formulacja"], (9, "Zgodnie z etykietą")
        )[1]

        tank_table_rows.append(
            {
                "Kolejność wlewania": order_desc,
                "Preparat": prod["nazwa"],
                "Formulacja": prod["formulacja"],
                "Dawka na 1 ha": f"{prod['dawka_ha']} {prod['jednostka']}",
                f"Na 1 pełny zbiornik ({tank_capacity_l} l)": f"{per_full_tank} {unit_short}"
                if full_tanks_count > 0
                else "-",
                f"Na końcówkę ({remainder_liquid_l} l wody)": f"{per_remainder_tank} {unit_short}"
                if remainder_liquid_l > 0
                else "-",
                f"Łącznie na całe pole ({area_ha} ha)": f"{total_need} {unit_short}",
            }
        )

    st.markdown(
        "##### 🧪 Instrukcja mieszania (automatycznie posortowana wg fizykochemii formulacji):"
    )
    st.dataframe(
        pd.DataFrame(tank_table_rows), use_container_width=True, hide_index=True
    )

st.divider()

# ==========================================
# 7. MODUŁ 3: TABELA EWIDENCJI UE 2023/564 (AUTOMATYCZNY GENERATOR)
# ==========================================
st.header("📋 Moduł 3: Gotowy Wpis do Elektronicznej Ewidencji Zabiegów (Standard UE 2023/564)")
st.caption(
    "Zgodnie z rozporządzeniem KE (UE) 2023/564 każdy zastosowany Środek Ochrony Roślin w mieszaninie zbiornikowej "
    "musi zostać wykazany w osobnym wierszu wraz z numerem zezwolenia MRiRW oraz kodem EPPO uprawy."
)

sor_only_list = [p for p in chosen_products_configured if p["is_sor"]]

if not sor_only_list:
    st.info("Wybierz przynajmniej jeden Środek Ochrony Roślin w Module 2, aby wygenerować wiersze ewidencji urzędowej.")
else:
    eu_records = []
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for sor_prod in sor_only_list:
        eu_records.append(
            {
                "1. Data i godz. rozpoczęcia": current_timestamp,
                "2. Lokalizacja / Działka": parcel_id,
                "3. Uprawa (Nazwa)": selected_crop,
                "4. Kod EPPO uprawy": eppo_crop_code,
                "5. Faza BBCH": selected_bbch.split(" ")[0] + " " + selected_bbch.split(" ")[1],
                "6. Powierzchnia (ha)": area_ha,
                "7. Pełna nazwa ŚOR": sor_prod["nazwa"],
                "8. Nr zezwolenia MRiRW": sor_prod["nr_zezwolenia"],
                "9. Zastosowana dawka": f"{sor_prod['dawka_ha']} {sor_prod['jednostka']}",
                "10. Przyczyna zabiegu (Agrofag)": selected_pest,
                "11. Warunki pogodowe (Auto-IMGW)": f"T: {temp_c}°C, RH: {rh}%, Wiatr: {wind_ms} m/s, ΔT: {delta_t}°C ({selected_station_name})",
            }
        )

    df_eu_preview = pd.DataFrame(eu_records)
    st.dataframe(df_eu_preview, use_container_width=True, hide_index=True)

    # Przycisk pobrania gotowego pliku CSV (otwieralnego w Excelu z polskimi znakami UTF-8-SIG)
    csv_bytes = df_eu_preview.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Pobierz wygenerowaną ewidencję zabiegu (Plik CSV / Excel)",
        data=csv_bytes,
        file_name=f"ewidencja_sor_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
