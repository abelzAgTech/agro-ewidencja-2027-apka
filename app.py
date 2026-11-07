import math
import os
import re
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
# 2. SŁOWNIKI DANYCH (EPPO, BBCH, BAZA BAZOWA ŚOR)
# ==========================================

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
            "Mszyce zbożowe - wektory wirusów (SITAVE)",
            "Septorioza paskowana liści (ZIMYTR)",
            "Mączniak prawdziwy zbóż (BLUMGR)",
            "Fuzarioza kłosów (FUSASP)",
            "Łamliwość źdźbła zbóż (OCULHE)",
            "Regulacja pokroju / skracanie źdźbła (PGR)",
        ],
    },
    "Pszenica jara": {
        "eppo_code": "TRZAX",
        "bbch_stages": [
            "BBCH 12-29 (Rozwój liści i krzewienie)",
            "BBCH 30-37 (Strzelanie w źdźbło)",
            "BBCH 39-59 (Liść flagowy i kłoszenie)",
            "BBCH 61-69 (Kwitnienie)",
        ],
        "pests": [
            "Chwasty dwuliścienne (TTTDD)",
            "Owies głuchy (AVEFA)",
            "Skrzypionki zbożowe (LEMAOR)",
            "Septorioza i rdze zbożowe (PUCCRT)",
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
            "Samosiewy zbóż w rzepaku (GRAMI)",
            "Chowacz brukwiaczek (CEUTNA)",
            "Chowacz czterozębny (CEUTPA)",
            "Słodyszek rzepakowy (MELIAE)",
            "Chowacz podobnik i pryszczarek kapustnik (CEUTAS)",
            "Zgnilizna twardzikowa (SCLESC)",
            "Sucha zgnilizna kapustnych + regulacja pokroju (LEPTMA)",
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
            "Chwastnica jednostronna i chwasty dwuliścienne (ECHCG)",
            "Komosa biała i szarłat szorstki (CHEAL)",
            "Omacnica prosowianka (OSTRNU)",
            "Zachodnia stonka kukurydziana (DIABVI)",
            "Ploniarka zbożówka (OSCIFF)",
        ],
    },
    "Jęczmień ozimy / jary": {
        "eppo_code": "HORVX",
        "bbch_stages": [
            "BBCH 10-29 (Wschody i krzewienie)",
            "BBCH 30-32 (1-2 kolanko)",
            "BBCH 37-39 (Liść podflagowy i flagowy)",
            "BBCH 51-59 (Kłoszenie)",
        ],
        "pests": [
            "Chwasty dwuliścienne i miotła zbożowa (TTTDD)",
            "Plamistość siatkowa jęczmienia (PYRNTE)",
            "Rynchosporioza zbóż (RHYNSE)",
            "Skrzypionki zbożowe (LEMAOR)",
            "Mszyce zbożowe (SITAVE)",
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
    "Burak cukrowy": {
        "eppo_code": "BEAVA",
        "bbch_stages": [
            "BBCH 10-14 (Faza liścieni do 4 liści - zabiegi dzielone)",
            "BBCH 15-19 (Rozwój rozety liściowej)",
            "BBCH 31-39 (Zwieranie międzyrzędzi)",
        ],
        "pests": [
            "Chwasty dwuliścienne w buraku (TTTDD)",
            "Chwasty jednoliścienne / prosowate (GRAMI)",
            "Chwościk buraka (CERCBE)",
            "Mszyca burakowa i śmietka (APHIBA)",
        ],
    },
    "Soja / Groch / Bobowate": {
        "eppo_code": "GLXMA",
        "bbch_stages": [
            "BBCH 00-08 (Przedwschodowo doglebowo)",
            "BBCH 12-16 (Rozwój trójlistków / wąsów)",
            "BBCH 51-65 (Pąkowanie i kwitnienie)",
        ],
        "pests": [
            "Chwasty dwuliścienne i jednoliścienne (TTTMM)",
            "Oprzędziki i mszyce (SITOLI)",
            "Zgnilizna twardzikowa i askochytoza (SCLESC)",
        ],
    },
    "Pomidor / Papryka / Ogórek": {
        "eppo_code": "LYPES",
        "bbch_stages": [
            "BBCH 12-19 (Rozwój liści po wysadzeniu)",
            "BBCH 51-69 (Kwitnienie kolejnych gron)",
            "BBCH 71-89 (Rozwój i dojrzewanie owoców)",
        ],
        "pests": [
            "Zaraza ziemniaka i mączniak rzekomy (PHYTIN)",
            "Szara pleśń i alternarioza (BOTRCI)",
            "Mszyce, wciornastki i mączliki (TRIAVA)",
        ],
    },
}

FORMULATION_MIXING_ORDER = {
    "KOND": (1, "1. Kondycjoner wody / Bufor pH (przed wszystkimi środkami)"),
    "WG": (2, "2. Granulaty do sporządzania zawiesiny (WG / SG)"),
    "SG": (2, "2. Granulaty rozpuszczalne w wodzie (SG)"),
    "SP": (2, "2. Proszki rozpuszczalne w wodzie (SP)"),
    "WP": (2, "2. Proszki do sporządzania zawiesiny (WP)"),
    "CS": (3, "3. Zawiesiny kapsuł (CS)"),
    "SC": (3, "3. Koncentraty stężonych zawiesin (SC)"),
    "SE": (3, "3. Zawiesino-emulsje (SE)"),
    "OD": (3, "3. Zawiesiny olejowe (OD)"),
    "SL": (4, "4. Koncentraty rozpuszczalne w wodzie (SL)"),
    "EW": (5, "5. Emulsje olej w wodzie (EW)"),
    "EC": (5, "5. Koncentraty do sporządzania emulsji wodnej (EC)"),
    "NAW": (6, "6. Nawozy dolistne i mikroelementy"),
    "ADI": (7, "7. Adiuwanty olejowe i zwilżacze (na sam koniec)"),
}

DEFAULT_SOR_DB = [
    {"nazwa": "Chwastox Trio 540 SL", "nr_zezwolenia": "R-110/2014", "kategoria": "Herbicyd", "substancja": "mekoprop-P + MCPA + dikamba", "formulacja": "SL", "dawka_domyslna": 2.0, "jednostka": "l/ha"},
    {"nazwa": "Mustang Forte 195 SE", "nr_zezwolenia": "R-122/2011", "kategoria": "Herbicyd", "substancja": "florasulam + aminopyralid + 2,4-D", "formulacja": "SE", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Axial 50 EC", "nr_zezwolenia": "R-108/2019", "kategoria": "Herbicyd", "substancja": "pinoksaden (50 g/l)", "formulacja": "EC", "dawka_domyslna": 0.9, "jednostka": "l/ha"},
    {"nazwa": "Puma Uniwersal 069 EW", "nr_zezwolenia": "R-121/2014", "kategoria": "Herbicyd", "substancja": "fenoksaprop-P-etylu (69 g/l)", "formulacja": "EW", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Stomp Aqua 455 CS", "nr_zezwolenia": "R-133/2013", "kategoria": "Herbicyd", "substancja": "pendimetalina (455 g/l)", "formulacja": "CS", "dawka_domyslna": 2.5, "jednostka": "l/ha"},
    {"nazwa": "Boxer 800 EC", "nr_zezwolenia": "R-107/2013", "kategoria": "Herbicyd", "substancja": "prosulfokarb (800 g/l)", "formulacja": "EC", "dawka_domyslna": 3.0, "jednostka": "l/ha"},
    {"nazwa": "Bizon", "nr_zezwolenia": "R-93/2017", "kategoria": "Herbicyd", "substancja": "diflufenikan + florasulam + penoksulam", "formulacja": "SC", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Lancet Plus 125 WG", "nr_zezwolenia": "R-139/2012", "kategoria": "Herbicyd", "substancja": "florasulam + piroksysulam + aminopyralid", "formulacja": "WG", "dawka_domyslna": 0.2, "jednostka": "kg/ha"},
    {"nazwa": "Butisan Star 416 SC", "nr_zezwolenia": "R-109/2012", "kategoria": "Herbicyd", "substancja": "metazachlor + chinomerak", "formulacja": "SC", "dawka_domyslna": 2.5, "jednostka": "l/ha"},
    {"nazwa": "Maister Power 42,5 OD", "nr_zezwolenia": "R-45/2013", "kategoria": "Herbicyd", "substancja": "foramsulfuron + jodosulfuron + tienkarbazon", "formulacja": "OD", "dawka_domyslna": 1.5, "jednostka": "l/ha"},
    {"nazwa": "Lumax 537,5 SE", "nr_zezwolenia": "R-66/2011", "kategoria": "Herbicyd", "substancja": "mezotrion + S-metolachlor + terbutylazyna", "formulacja": "SE", "dawka_domyslna": 3.5, "jednostka": "l/ha"},
    {"nazwa": "Agil-S 100 EC", "nr_zezwolenia": "R-76/2012", "kategoria": "Herbicyd", "substancja": "propachizafop (100 g/l)", "formulacja": "EC", "dawka_domyslna": 0.7, "jednostka": "l/ha"},
    {"nazwa": "Roundup Flex 480", "nr_zezwolenia": "R-135/2013", "kategoria": "Herbicyd", "substancja": "glifosat (480 g/l)", "formulacja": "SL", "dawka_domyslna": 2.25, "jednostka": "l/ha"},
    {"nazwa": "Tebu 250 EW", "nr_zezwolenia": "R-71/2014", "kategoria": "Fungicyd", "substancja": "tebukonazol (250 g/l)", "formulacja": "EW", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Amistar 250 SC", "nr_zezwolenia": "R-98/2011", "kategoria": "Fungicyd", "substancja": "azoksystrobina (250 g/l)", "formulacja": "SC", "dawka_domyslna": 0.8, "jednostka": "l/ha"},
    {"nazwa": "Input 460 EC", "nr_zezwolenia": "R-112/2012", "kategoria": "Fungicyd", "substancja": "protiokonazol + spiroksamina", "formulacja": "EC", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Priaxor EC", "nr_zezwolenia": "R-162/2015", "kategoria": "Fungicyd", "substancja": "fluksapyroksad + piraklostrobina", "formulacja": "EC", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Elatus Era", "nr_zezwolenia": "R-29/2017", "kategoria": "Fungicyd", "substancja": "benzowindyflupyr + protiokonazol", "formulacja": "EC", "dawka_domyslna": 1.0, "jednostka": "l/ha"},
    {"nazwa": "Pictor 400 SC", "nr_zezwolenia": "R-77/2012", "kategoria": "Fungicyd", "substancja": "boskalid + dimoksystrobina", "formulacja": "SC", "dawka_domyslna": 0.5, "jednostka": "l/ha"},
    {"nazwa": "Revus 250 SC", "nr_zezwolenia": "R-55/2011", "kategoria": "Fungicyd", "substancja": "mandipropamid (250 g/l)", "formulacja": "SC", "dawka_domyslna": 0.6, "jednostka": "l/ha"},
    {"nazwa": "Mospilan 20 SP", "nr_zezwolenia": "R-367/2014d", "kategoria": "Insektycyd", "substancja": "acetamipryd (20%)", "formulacja": "SP", "dawka_domyslna": 0.12, "jednostka": "kg/ha"},
    {"nazwa": "Inazuma 130 WG", "nr_zezwolenia": "R-91/2015", "kategoria": "Insektycyd", "substancja": "acetamipryd + lambda-cyhalotryna", "formulacja": "WG", "dawka_domyslna": 0.20, "jednostka": "kg/ha"},
    {"nazwa": "Karate Zeon 050 CS", "nr_zezwolenia": "R-85/2012", "kategoria": "Insektycyd", "substancja": "lambda-cyhalotryna (50 g/l)", "formulacja": "CS", "dawka_domyslna": 0.15, "jednostka": "l/ha"},
    {"nazwa": "Moddus 250 EC", "nr_zezwolenia": "R-44/2011", "kategoria": "Regulator wzrostu", "substancja": "trineksapak etylu (250 g/l)", "formulacja": "EC", "dawka_domyslna": 0.4, "jednostka": "l/ha"},
]

FOLIAR_ADDITIVES_DB = {
    "Mocznik (46% N - dokarmianie dolistne)": {"formulacja": "NAW", "dawka_domyslna": 12.0, "jednostka": "kg/ha"},
    "Siarczan magnezu siedmiowodny (16% MgO + 32% SO3)": {"formulacja": "NAW", "dawka_domyslna": 5.0, "jednostka": "kg/ha"},
    "Nawóz wieloskładnikowy NPK 20-20-20 + mikro": {"formulacja": "NAW", "dawka_domyslna": 3.0, "jednostka": "kg/ha"},
    "Siarczan amonu (Kondycjoner twardej wody / Bufor pH)": {"formulacja": "KOND", "dawka_domyslna": 0.5, "jednostka": "kg/ha"},
    "Adiuwant zmniejszający napięcie powierzchniowe / antydryfowy": {"formulacja": "ADI", "dawka_domyslna": 0.15, "jednostka": "l/ha"},
}


# ==========================================
# 3. PARSER BAZY MRiRW (ETAP 3.5)
# ==========================================
def detect_formulation_and_unit(name_str: str):
    """Wyciąga kod formulacji (SL, EC, WG itp.) oraz jednostkę z nazwy handlowej ŚOR."""
    upper_name = str(name_str).upper()
    solid_forms = ["WG", "SG", "SP", "WP"]
    liquid_forms = ["SL", "EC", "EW", "SC", "CS", "SE", "OD"]

    for f in solid_forms:
        if re.search(rf"\b{f}\b", upper_name):
            return f, "kg/ha", 0.25
    for f in liquid_forms:
        if re.search(rf"\b{f}\b", upper_name):
            return f, "l/ha", 1.0
    return "SC", "l/ha", 1.0


def parse_mrirw_dataframe(df: pd.DataFrame) -> list:
    """Przetwarza surowy arkusz MRiRW (~30 000 wierszy) na zdeduplikowaną listę unikalnych ŚOR."""
    cols_lower = {str(c).lower().strip(): c for c in df.columns}

    name_col = next((orig for low, orig in cols_lower.items() if "nazwa" in low), None)
    perm_col = next((orig for low, orig in cols_lower.items() if "zezw" in low or "nr" in low), None)
    cat_col = next((orig for low, orig in cols_lower.items() if "rodzaj" in low or "typ" in low), None)
    sub_col = next((orig for low, orig in cols_lower.items() if "substancj" in low or "skład" in low), None)

    if not name_col or not perm_col:
        return []

    # Usuwamy duplikaty po nazwie handlowej (w pliku MRiRW każdy środek występuje wiele razy dla różnych upraw)
    df_clean = df.dropna(subset=[name_col, perm_col]).drop_duplicates(subset=[name_col])

    parsed_list = []
    for _, row in df_clean.iterrows():
        nazwa = str(row[name_col]).strip()
        nr_zezw = str(row[perm_col]).strip()
        if not nazwa or nazwa.lower() == "nan":
            continue

        kategoria = str(row[cat_col]).strip() if cat_col and pd.notna(row[cat_col]) else "ŚOR (MRiRW)"
        substancja = str(row[sub_col]).strip() if sub_col and pd.notna(row[sub_col]) else "Wg etykiety"
        form, unit, def_dose = detect_formulation_and_unit(nazwa)

        parsed_list.append(
            {
                "nazwa": nazwa,
                "nr_zezwolenia": nr_zezw,
                "kategoria": kategoria,
                "substancja": substancja,
                "formulacja": form,
                "dawka_domyslna": def_dose,
                "jednostka": unit,
            }
        )
    return parsed_list


@st.cache_data(show_spinner=False)
def load_local_mrirw_registry():
    """Automatycznie wczytuje plik rejestr_sor.xlsx lub rejestr_sor.csv z repozytorium GitHub, jeśli istnieje."""
    for filename in ["rejestr_sor.xlsx", "rejestr_sor.csv"]:
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename) if filename.endswith(".csv") else pd.read_excel(filename)
                parsed = parse_mrirw_dataframe(df)
                if parsed:
                    return parsed, f"Wczytano pełny rejestr MRiRW z pliku `{filename}` ({len(parsed)} unikalnych środków)"
            except Exception as e:
                return None, f"Błąd odczytu `{filename}`: {e}"
    return None, None


# ==========================================
# 4. FUNKCJE FIZYCZNE, POGODOWE I SMART-ULDK (NAPRAWA 150/1)
# ==========================================
def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_wet_bulb_stull(temp_c: float, rh: float) -> float:
    rh = max(5.0, min(99.0, rh))
    term1 = temp_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
    term2 = math.atan(temp_c + rh)
    term3 = math.atan(rh - 1.676331)
    term4 = 0.00391838 * (rh**1.5) * math.atan(0.023101 * rh)
    tw = term1 + term2 - term3 + term4 - 4.686035
    return round(tw, 2)


def calculate_delta_t(temp_c: float, rh: float) -> float:
    tw = calculate_wet_bulb_stull(temp_c, rh)
    return round(temp_c - tw, 1)


@st.cache_data(ttl=1800)
def fetch_imgw_synop_data():
    url = "https://danepubliczne.imgw.pl/api/data/synop"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


def calculate_wkt_area_ha(wkt_str: str) -> float:
    """Wylicza powierzchnię działki w hektarach (ha) z geometrii WKT (EPSG:2180) ze wzoru Gaussa."""
    if not wkt_str or "POLYGON" not in wkt_str.upper():
        return 0.0

    rings = re.findall(r"\(([^()]+)\)", wkt_str)
    if not rings:
        return 0.0

    total_area_m2 = 0.0
    for idx, ring in enumerate(rings):
        pts = []
        for pair in ring.split(","):
            coords = pair.strip().split()
            if len(coords) >= 2:
                try:
                    pts.append((float(coords[0]), float(coords[1])))
                except ValueError:
                    continue

        if len(pts) < 3:
            continue

        ring_area = 0.0
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            ring_area += x1 * y2 - x2 * y1
        ring_area = abs(ring_area) / 2.0

        if idx == 0:
            total_area_m2 += ring_area
        else:
            total_area_m2 -= ring_area

    return round(max(0.01, total_area_m2 / 10000.0), 2)


def parse_uldk_parcel_lines(text_response: str) -> list:
    """Parsuje wiersze odpowiedzi z GUGiK ULDK do listy słowników z wyliczoną powierzchnią."""
    lines = [line.strip() for line in text_response.splitlines() if line.strip()]
    data_lines = [l for l in lines if "|" in l and "POLYGON" in l.upper()]
    results = []
    for row in data_lines:
        parts = row.split("|")
        if len(parts) >= 7:
            teryt, voiv, county, commune, region, parcel_nr, geom_wkt = parts[:7]
            area_ha = calculate_wkt_area_ha(geom_wkt)
            results.append(
                {
                    "teryt": teryt,
                    "wojewodztwo": voiv,
                    "powiat": county,
                    "gmina": commune,
                    "obreb": region,
                    "nr_dzialki": parcel_nr,
                    "area_ha": area_ha,
                    "label": f"{region} - dz. nr {parcel_nr} ({area_ha} ha) | TERYT: {teryt} [gm. {commune}, pow. {county}]",
                }
            )
    return results


@st.cache_data(ttl=3600)
def query_gugik_uldk(search_mode: str, query_val: str):
    """Dwuetapowy algorytm Smart-ULDK obsługujący działki po podziale (np. Wola Dalsza 150/1) oraz arkusze AR_."""
    base_url = "https://uldk.gugik.gov.pl/"
    q_clean = query_val.strip()

    try:
        if search_mode == "xy":
            params = {
                "request": "GetParcelByXY",
                "xy": q_clean,
                "result": "teryt,voivodeship,county,commune,region,parcel,geom_wkt",
                "srid": "2180",
            }
            resp = requests.get(base_url, params=params, timeout=12)
            results = parse_uldk_parcel_lines(resp.text)
            if results:
                return results, None
            return [], f"Nie znaleziono działki dla współrzędnych GPS: {q_clean}"

        # KROK A: Jeśli użytkownik podał od razu tekst типа "Wola Dalsza 150/1",
        # rozbijamy go na nazwę obrębu ("Wola Dalsza") oraz numer działki ("150/1")
        match = re.match(r"^(.+?)\s+([0-9]+[0-9a-zA-Z/\.-]*)$", q_clean)
        if match and not re.match(r"^\d{6}_", q_clean):
            region_name = match.group(1).strip()
            parcel_nr = match.group(2).strip()

            # 1. Pobieramy dokładny kod TERYT obrębu z usługi GetRegionByIdOrNr
            reg_params = {
                "request": "GetRegionByIdOrNr",
                "id": region_name,
                "result": "teryt,region,commune,county",
            }
            reg_resp = requests.get(base_url, params=reg_params, timeout=10)
            reg_lines = [l.strip() for l in reg_resp.text.splitlines() if "|" in l]

            found_parcels = []
            for r_line in reg_lines[:6]:
                reg_teryt = r_line.split("|")[0].strip()
                # Sprawdzamy zarówno bezpośredni kod TERYT.NR (np. 181002_2.0007.150/1),
                # jak i warianty z arkuszem ewidencyjnym AR_1, AR_2
                candidate_ids = [
                    f"{reg_teryt}.{parcel_nr}",
                    f"{reg_teryt}.AR_1.{parcel_nr}",
                    f"{reg_teryt}.AR_2.{parcel_nr}",
                ]
                for cid in candidate_ids:
                    # Budujemy URL z niezakodowanym znakiem '/', czego wymagają niektóre serwery GUGiK
                    direct_url = (
                        f"{base_url}?request=GetParcelByIdOrNr&id={cid}"
                        f"&result=teryt,voivodeship,county,commune,region,parcel,geom_wkt&srid=2180"
                    )
                    p_resp = requests.get(direct_url, timeout=8)
                    parsed = parse_uldk_parcel_lines(p_resp.text)
                    if parsed:
                        found_parcels.extend(parsed)
                        break

            if found_parcels:
                return found_parcels, None

        # KROK B: Standardowe zapytanie bezpośrednie (gdy wpisano pełny TERYT lub prostą nazwę)
        params = {
            "request": "GetParcelByIdOrNr",
            "id": q_clean,
            "result": "teryt,voivodeship,county,commune,region,parcel,geom_wkt",
            "srid": "2180",
        }
        resp = requests.get(base_url, params=params, timeout=12)
        results = parse_uldk_parcel_lines(resp.text)
        if results:
            return results, None

        # KROK C: Jeśli działka z ukośnikiem (np. 150/1) nadal nie istnieje w GUGiK (np. świeży podział niezsynchronizowany
        # przez starostwo lub inny numer podziałowy), sprawdzamy działkę macierzystą przed ukośnikiem (np. 150)
        if "/" in q_clean:
            base_query = q_clean.split("/")[0].strip()
            base_results, _ = query_gugik_uldk("name", base_query)
            if base_results:
                return (
                    base_results,
                    f"Uwaga: W bazie GUGiK nie figuruje jeszcze podział `{q_clean}` (lub ma inny numer arkusza). "
                    f"Załadowano działkę sąsiednią/macierzystą `{base_query}` – możesz ręcznie skorygować jej numer i ha poniżej.",
                )

        return [], f"Nie znaleziono działki `{q_clean}` w bazie GUGiK ULDK."
    except Exception as e:
        return [], f"Błąd połączenia z serwerem GUGiK ULDK: {e}"


# ==========================================
# 5. INICJALIZACJA PAMIĘCI SESJI (SESSION STATE)
# ==========================================
local_sor_list, local_sor_msg = load_local_mrirw_registry()

if "sor_db" not in st.session_state:
    if local_sor_list:
        st.session_state.sor_db = local_sor_list
        st.session_state.sor_source_info = local_sor_msg
    else:
        st.session_state.sor_db = DEFAULT_SOR_DB.copy()
        st.session_state.sor_source_info = f"Wbudowana baza startowa ({len(DEFAULT_SOR_DB)} najpopularniejszych ŚOR). Wgraj plik `rejestr_sor.xlsx` na GitHuba, aby mieć ~2800 środków."

if "parcel_id_input" not in st.session_state:
    st.session_state.parcel_id_input = "181002_2.0007.150/1 (Wola Dalsza - dz. 150/1)"

if "area_ha_input" not in st.session_state:
    st.session_state.area_ha_input = 1.50

if "uldk_results" not in st.session_state:
    st.session_state.uldk_results = []

if "eu_log_history" not in st.session_state:
    st.session_state.eu_log_history = []


# ==========================================
# 6. NAGŁÓWEK APLIKACJI
# ==========================================
st.title("🚜 AgroCompliance 2027: Asystent Oprysków i Ewidencji ŚOR")
st.markdown(
    "**Wersja rozwojowa v0.4.5** | Moduł 1: Radar IMGW & Delta-T | "
    "Moduł 2: Smart-ULDK (obsługa podziałów `/`) + Pełny Rejestr MRiRW + Tank-Mix | "
    "Moduł 3: Wielopolowy Dziennik Ewidencji UE 2023/564"
)
st.divider()

# ==========================================
# 7. MODUŁ 1: RADAR OKNA OPRYSKOWEGO (IMGW + DELTA-T)
# ==========================================
st.header("📡 Moduł 1: Warunki Pogodowe i Fizykochemia Kropli (Delta-T)")

data, error = fetch_imgw_synop_data()
col_select, col_manual = st.columns([1, 1])

with col_select:
    st.subheader("1. Stacja meteorologiczna IMGW-PIB")
    if error or not data:
        st.warning(f"Nie udało się pobrać danych z IMGW ({error}). Użyj suwaków obok.")
        selected_station_name = "Tryb ręczny"
        default_temp, default_rh, default_wind = 18.0, 60.0, 2.5
    else:
        station_dict = {item["stacja"]: item for item in data if "stacja" in item}
        station_names = sorted(list(station_dict.keys()))
        default_index = station_names.index("Rzeszów") if "Rzeszów" in station_names else 0

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
    st.caption("W razie potrzeby skoryguj dane ze stacji własnym pomiarem z pola:")
    c1, c2, c3 = st.columns(3)
    with c1:
        temp_c = st.number_input("Temperatura (°C)", min_value=-10.0, max_value=45.0, value=default_temp, step=0.5)
    with c2:
        rh = st.number_input("Wilgotność (%)", min_value=5.0, max_value=100.0, value=default_rh, step=1.0)
    with c3:
        wind_ms = st.number_input("Wiatr (m/s)", min_value=0.0, max_value=25.0, value=default_wind, step=0.5)

delta_t = calculate_delta_t(temp_c, rh)
wind_kmh = round(wind_ms * 3.6, 1)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Wskaźnik Delta-T", f"{delta_t} °C", "Optimum: 2.0 - 8.0 °C", delta_color="normal" if 2.0 <= delta_t <= 8.0 else "inverse")
with m2:
    st.metric("Prędkość wiatru", f"{wind_ms} m/s ({wind_kmh} km/h)", "Max prawny: 4.0 m/s", delta_color="normal" if wind_ms <= 4.0 else "inverse")
with m3:
    st.metric("Temperatura", f"{temp_c} °C", "Optimum: 10 - 25 °C", delta_color="normal" if 10.0 <= temp_c <= 25.0 else "off")
with m4:
    st.metric("Wilgotność względna", f"{rh} %", "Optimum: powyżej 50%", delta_color="normal" if rh >= 50.0 else "off")

reasons_stop, reasons_warn = [], []
if wind_ms > 4.0:
    reasons_stop.append(f"❌ **PRZEKROCZONY LIMIT WIATRU ({wind_ms} m/s):** Zabieg prawnie zabroniony (ryzyko znoszenia cieczy i mandatu PIORiN).")
elif wind_ms > 3.0:
    reasons_warn.append(f"⚠️ **Podwyższony wiatr ({wind_ms} m/s):** Zalecane użycie rozpylaczy eżektorowych (antydryfowych).")

if delta_t > 10.0:
    reasons_stop.append(f"❌ **KRYTYCZNE DELTA-T ({delta_t} °C):** Ekstremalnie szybkie odparowywanie kropli w locie! Ryzyko poparzenia roślin.")
elif delta_t > 8.0:
    reasons_warn.append(f"⚠️ **Wysokie Delta-T ({delta_t} °C):** Krople szybko parują. Zwiększ wydatek wody lub dodaj adiuwant.")
elif delta_t < 2.0:
    reasons_warn.append(f"⚠️ **Niskie Delta-T ({delta_t} °C):** Krople mogą spływać z liści (powietrze nasycone parą wodną).")

if temp_c > 25.0:
    reasons_warn.append(f"⚠️ **Wysoka temperatura ({temp_c} °C):** Ryzyko fitotoksyczności (szczególnie z mocznikiem i herbicydami).")

if reasons_stop:
    st.error("### 🛑 ZAKAZ OPRYSKU – Warunki niedopuszczalne!")
    for r in reasons_stop + reasons_warn:
        st.markdown(r)
elif reasons_warn:
    st.warning("### ⚠️ OPRYSK WARUNKOWY – Zachowaj ostrożność!")
    for w in reasons_warn:
        st.markdown(w)
else:
    st.success("### ✅ ZIELONE ŚWIATŁO – Idealne okno pogodowe na zabieg!")

st.divider()

# ==========================================
# 8. MODUŁ 2: SMART-ULDK, PEŁNA BAZA ŚOR I KALKULATOR ZBIORNIKA
# ==========================================
st.header("🗺️ Moduł 2: Geolokalizacja Działki (Smart-ULDK), Słownik EPPO i Tank-Mix")

with st.container(border=True):
    st.subheader("🛰️ A. Automatyczne pobieranie działki i powierzchni z serwera GUGiK ULDK")
    st.caption(
        "Dwuetapowy silnik Smart-ULDK: wpisz nazwę miejscowości i numer działki (także z ukośnikiem po podziale, np. `Wola Dalsza 150/1`). "
        "System najpierw pobierze kod TERYT obrębu, a następnie odpyta tabelę katastralną o dokładną geometrię działki."
    )

    uldk_tab1, uldk_tab2 = st.tabs(
        ["🔍 Szukaj po nazwie obrębu i nr działki (np. Wola Dalsza 150/1)", "📍 Szukaj po współrzędnych GPS (WGS84)"]
    )

    with uldk_tab1:
        u_col1, u_col2 = st.columns([3, 1])
        with u_col1:
            uldk_query_text = st.text_input(
                "Obręb i numer działki (lub kod TERYT):",
                value="Wola Dalsza 150/1",
                placeholder="np. Wola Dalsza 150/1 lub 181002_2.0007.150/1",
            )
        with u_col2:
            st.write("")
            if st.button("🔎 Wyszukaj w GUGiK", use_container_width=True):
                results, warn_or_err = query_gugik_uldk("name", uldk_query_text)
                if warn_or_err and not results:
                    st.error(warn_or_err)
                    st.session_state.uldk_results = []
                else:
                    if warn_or_err:
                        st.warning(warn_or_err)
                    st.session_state.uldk_results = results
                    if len(results) == 1:
                        r = results[0]
                        st.session_state.parcel_id_input = f"{r['teryt']} ({r['obreb']} - dz. {r['nr_dzialki']})"
                        st.session_state.area_ha_input = r["area_ha"]
                        st.success(f"Pobrano z GUGiK: **{r['label']}** i zaktualizowano powierzchnię!")

    with uldk_tab2:
        g_col1, g_col2, g_col3 = st.columns([1.5, 1.5, 1])
        with g_col1:
            gps_lat = st.number_input("Szerokość geogr. (Lat N):", value=50.1165, format="%.5f", step=0.001)
        with g_col2:
            gps_lon = st.number_input("Długość geogr. (Lon E):", value=22.2540, format="%.5f", step=0.001)
        with g_col3:
            st.write("")
            if st.button("📍 Znajdź działkę po GPS", use_container_width=True):
                xy_param = f"{gps_lon},{gps_lat},4326"
                results, err = query_gugik_uldk("xy", xy_param)
                if err:
                    st.error(err)
                elif results:
                    r = results[0]
                    st.session_state.uldk_results = results
                    st.session_state.parcel_id_input = f"{r['teryt']} ({r['obreb']} - dz. {r['nr_dzialki']})"
                    st.session_state.area_ha_input = r["area_ha"]
                    st.success(f"Namierzono działkę z GPS: **{r['label']}**")

    if len(st.session_state.uldk_results) > 1:
        st.info(f"Znaleziono {len(st.session_state.uldk_results)} pasujących działek w bazie GUGiK. Wybierz właściwą:")
        sel_col1, sel_col2 = st.columns([3, 1])
        with sel_col1:
            chosen_idx = st.selectbox(
                "Wybierz działkę z listy wyników GUGiK:",
                options=range(len(st.session_state.uldk_results)),
                format_func=lambda i: st.session_state.uldk_results[i]["label"],
            )
        with sel_col2:
            st.write("")
            if st.button("✅ Załaduj wybraną działkę", use_container_width=True):
                r = st.session_state.uldk_results[chosen_idx]
                st.session_state.parcel_id_input = f"{r['teryt']} ({r['obreb']} - dz. {r['nr_dzialki']})"
                st.session_state.area_ha_input = r["area_ha"]
                st.rerun()

# Zarządzanie bazą ŚOR (Etap 3.5)
with st.expander(f"📦 Baza ŚOR MRiRW (Aktywnych środków: {len(st.session_state.sor_db)}) – Zarządzaj lub wgraj pełny rejestr"):
    st.info(st.session_state.sor_source_info)
    tab_excel_sor, tab_manual_sor = st.tabs(
        ["📥 Wgraj pełny plik Excel (.xlsx) z dane.gov.pl", "➕ Dopisz pojedynczy środek ręcznie"]
    )

    with tab_excel_sor:
        st.caption(
            "Jeśli wrzucisz plik `rejestr_sor.xlsx` bezpośrednio do swojego repozytorium na GitHubie, załaduje się on automatycznie przy każdym starcie. "
            "Możesz też przeciągnąć go tutaj ręcznie na czas bieżącej sesji:"
        )
        uploaded_file = st.file_uploader(
            "Wybierz oficjalny plik .xlsx lub .csv pobrany z dane.gov.pl", type=["xlsx", "csv"]
        )
        if uploaded_file is not None:
            try:
                df_mrirw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                parsed_sor = parse_mrirw_dataframe(df_mrirw)
                if parsed_sor:
                    st.session_state.sor_db = parsed_sor
                    st.session_state.sor_source_info = f"Wczytano z pliku użytkownika `{uploaded_file.name}` ({len(parsed_sor)} unikalnych ŚOR)"
                    st.success(
                        f"Przetworzono {len(df_mrirw)} wierszy z rejestru MRiRW i wyodrębniono **{len(parsed_sor)} unikalnych środków ochrony roślin**!"
                    )
                else:
                    st.warning("Nie rozpoznano kolumn z nazwą i numerem zezwolenia w tym pliku.")
            except Exception as e:
                st.error(f"Błąd podczas czytania pliku: {e}")

    with tab_manual_sor:
        mc1, mc2, mc3, mc4, mc5 = st.columns([2, 1.5, 1, 1, 1])
        with mc1:
            new_name = st.text_input("Pełna nazwa handlowa ŚOR", placeholder="np. Danadim 400 EC")
        with mc2:
            new_perm = st.text_input("Nr zezwolenia MRiRW", placeholder="np. R-121/2014")
        with mc3:
            new_form = st.selectbox("Formulacja", options=["SL", "EC", "EW", "SC", "CS", "SE", "OD", "WG", "SP", "WP"])
        with mc4:
            new_dose = st.number_input("Dawka domyślna", min_value=0.01, max_value=20.0, value=1.0, step=0.1)
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

# Główny formularz pola, uprawy (EPPO) i opryskiwacza
col_field, col_sprayer = st.columns([1, 1])

with col_field:
    st.subheader("🌾 B. Działka, Uprawa (EPPO) i Faza BBCH")

    parcel_id = st.text_input(
        "Identyfikator działki (automatycznie z GUGiK lub wpisz ręcznie):",
        key="parcel_id_input",
    )

    area_ha = st.number_input(
        "Powierzchnia zabiegu w ha (wyliczona z geometrii GUGiK lub skoryguj):",
        min_value=0.01,
        max_value=1000.0,
        step=0.10,
        key="area_ha_input",
    )

    selected_crop = st.selectbox(
        "Wybierz uprawę (automatyczne mapowanie kodu EPPO):",
        options=list(EPPO_CROPS_DB.keys()),
    )

    crop_info = EPPO_CROPS_DB[selected_crop]
    eppo_crop_code = crop_info["eppo_code"]
    st.info(f"🇪🇺 Wymagany kod unijny EPPO dla wybranej uprawy: **`{eppo_crop_code}`** ({selected_crop})")

    selected_bbch = st.selectbox(
        "Faza rozwojowa rośliny w skali BBCH:",
        options=crop_info["bbch_stages"],
    )

    selected_pest = st.selectbox(
        "Główna przyczyna zabiegu / zwalczany agrofag (z kodem EPPO):",
        options=crop_info["pests"],
    )

with col_sprayer:
    st.subheader("🚜 C. Parametry Opryskiwacza i Wybór Preparatów")

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
    all_sor_keys = list(sor_names_map.keys())
    default_sor_selection = [k for k in ["Chwastox Trio 540 SL", "Mospilan 20 SP"] if k in sor_names_map]
    if not default_sor_selection and all_sor_keys:
        default_sor_selection = [all_sor_keys[0]]

    selected_sor_names = st.multiselect(
        f"Wyszukaj i wybierz Środki Ochrony Roślin (w bazie: {len(sor_names_map)} pozycji):",
        options=all_sor_keys,
        default=default_sor_selection,
    )

    selected_foliar_names = st.multiselect(
        "Opcjonalnie: Dodaj nawozy dolistne / kondycjonery wody do zbiornika:",
        options=list(FOLIAR_ADDITIVES_DB.keys()),
        default=["Siarczan magnezu siedmiowodny (16% MgO + 32% SO3)"],
    )

# Konfiguracja dokładnych dawek dla wybranych produktów
st.subheader("⚖️ D. Dostosuj dawki na hektar i odbierz recepturę na zbiornik")

chosen_products_configured = []

if not selected_sor_names and not selected_foliar_names:
    st.warning("Wybierz przynajmniej jeden środek lub nawóz z listy powyżej, aby przeliczyć zbiornik.")
else:
    dose_cols = st.columns(min(4, max(1, len(selected_sor_names) + len(selected_foliar_names))))
    col_idx = 0

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
            st.caption(f"Zezw.: `{sor_item['nr_zezwolenia']}` | Form.: **{sor_item['formulacja']}**")
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
                    "nr_zezwolenia": "Nie dotyczy",
                    "formulacja": fol_item["formulacja"],
                    "dawka_ha": user_dose,
                    "jednostka": fol_item["jednostka"],
                    "is_sor": False,
                }
            )
        col_idx += 1

    # OBLICZENIA ZBIORNIKA OPRYSKIWACZA (TANK-MIX)
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
        st.metric("Wydajność 1 zbiornika", f"{max_ha_per_tank} ha", f"Przy {water_rate_l_ha} l/ha")
    with tm3:
        st.metric("Pełne zbiorniki", f"{full_tanks_count} szt.", f"Po {tank_capacity_l} l każdy")
    with tm4:
        if remainder_liquid_l > 0:
            st.metric("Końcówka (Ostatni zbiornik)", f"{remainder_liquid_l} l wody", f"Pokryje {remainder_ha} ha")
        else:
            st.metric("Końcówka (Ostatni zbiornik)", "Brak (0 l)", "Równy podział zbiorników")

    chosen_products_configured.sort(
        key=lambda x: FORMULATION_MIXING_ORDER.get(x["formulacja"], (9, "Inne"))[0]
    )

    tank_table_rows = []
    for prod in chosen_products_configured:
        unit_short = "l" if "l/" in prod["jednostka"] else "kg"
        total_need = round(prod["dawka_ha"] * area_ha, 2)
        per_full_tank = round(prod["dawka_ha"] * max_ha_per_tank, 2) if full_tanks_count > 0 else 0.0
        per_remainder_tank = round(prod["dawka_ha"] * remainder_ha, 2) if remainder_liquid_l > 0 else 0.0
        order_desc = FORMULATION_MIXING_ORDER.get(prod["formulacja"], (9, "Zgodnie z etykietą"))[1]

        tank_table_rows.append(
            {
                "Kolejność wlewania": order_desc,
                "Preparat": prod["nazwa"],
                "Formulacja": prod["formulacja"],
                "Dawka na 1 ha": f"{prod['dawka_ha']} {prod['jednostka']}",
                f"Na 1 pełny zbiornik ({tank_capacity_l} l)": f"{per_full_tank} {unit_short}" if full_tanks_count > 0 else "-",
                f"Na końcówkę ({remainder_liquid_l} l wody)": f"{per_remainder_tank} {unit_short}" if remainder_liquid_l > 0 else "-",
                f"Łącznie na całe pole ({area_ha} ha)": f"{total_need} {unit_short}",
            }
        )

    st.markdown("##### 🧪 Instrukcja mieszania (automatycznie posortowana wg fizykochemii formulacji):")
    st.dataframe(pd.DataFrame(tank_table_rows), use_container_width=True, hide_index=True)

st.divider()

# ==========================================
# 9. MODUŁ 3: WIELOPOLOWY DZIENNIK EWIDENCJI UE 2023/564
# ==========================================
st.header("📋 Moduł 3: Elektroniczny Dziennik Ewidencji Zabiegów (Standard UE 2023/564)")

sor_only_list = [p for p in chosen_products_configured if p["is_sor"]]

if not sor_only_list:
    st.info("Wybierz przynajmniej jeden Środek Ochrony Roślin w Module 2, aby przygotować wpis do ewidencji.")
else:
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    current_eu_records = []

    for sor_prod in sor_only_list:
        current_eu_records.append(
            {
                "1. Data i godz. rozpoczęcia": current_timestamp,
                "2. Identyfikator działki (TERYT / GUGiK)": parcel_id,
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

    st.subheader("🔹 Podgląd bieżącego zabiegu (przed dopisaniem do Dziennika):")
    st.dataframe(pd.DataFrame(current_eu_records), use_container_width=True, hide_index=True)

    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.button("➕ Dopisz bieżący zabieg do Dziennika Gospodarstwa", type="primary", use_container_width=True):
            st.session_state.eu_log_history.extend(current_eu_records)
            st.success(f"Dopisano {len(current_eu_records)} wiersz(e) dla działki **{parcel_id}** do Dziennika!")
    with b_col2:
        if st.session_state.eu_log_history and st.button("🗑️ Wyczyść zapisany Dziennik", use_container_width=True):
            st.session_state.eu_log_history = []
            st.rerun()

st.subheader(f"📚 Zbiorczy Dziennik Ewidencji Gospodarstwa (Zapisanych pozycji: {len(st.session_state.eu_log_history)})")

if st.session_state.eu_log_history:
    df_history = pd.DataFrame(st.session_state.eu_log_history)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    export_df = df_history
else:
    st.caption("Dziennik jest jeszcze pusty. Kliknij przycisk **'➕ Dopisz bieżący zabieg...'** powyżej, aby dodawać kolejne działki do wspólnej tabeli.")
    export_df = pd.DataFrame(current_eu_records) if sor_only_list else pd.DataFrame()

if not export_df.empty:
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Pobierz Ewidencję Zabiegów UE 2023/564 (Plik CSV / Excel)",
        data=csv_bytes,
        file_name=f"ewidencja_sor_2027_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
