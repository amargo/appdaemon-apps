# HydrologyData AppDaemon Integration

### Áttekintés
A HydrologyData egy AppDaemon alkalmazás, amely a Magyar Vízügyi Hatóság weboldaláról gyűjt és dolgoz fel hidrológiai adatokat. Az alkalmazás kinyeri a vízállás (cm) és a vízhőmérséklet (°C) értékeket, majd ezekhez megfelelő szenzorokat hoz létre a Home Assistantban.

### Követelmények
1. Telepített és konfigurált AppDaemon.
2. Python könyvtárak:
   - `requests`
   - `bs4` (BeautifulSoup4)
   - `fake_useragent`

### Konfiguráció
Az alábbi konfigurációt add hozzá az `apps.yaml` fájlhoz:

```yaml
HydrologyData:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "1649619E-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.agard_water_level
  water_level_friendly_name: "Agárd Water Level"
  water_temperature_entity: sensor.agard_water_temperature
  water_temperature_friendly_name: "Agárd Water Temperature"
```

- **`class`**: Az osztály neve a szkriptben.
- **`module`**: A Python modul neve (fájl `.py` kiterjesztés nélkül).
- **`allomas_voa`**: Az állomás azonosítója (VOA kód) az adatok lekéréséhez.
- **`water_level_entity`**: A vízállás szenzor Home Assistant entity ID-ja.
- **`water_level_friendly_name`**: A vízállás szenzor megjelenített neve.
- **`water_temperature_entity`**: A vízhőmérséklet szenzor Home Assistant entity ID-ja.
- **`water_temperature_friendly_name`**: A vízhőmérséklet szenzor megjelenített neve.
- **`verify_ssl`** *(opcionális, alapértelmezés: `true`)*: ellenőrizze-e a vizugy.hu tanúsítványát.
- **`allow_insecure_ssl_fallback`** *(opcionális, alapértelmezés: `false`)*: `SSLError` után egyszer próbálkozzon-e ellenőrzés nélkül. Lásd az [Ismert korlátok](#ismert-korlátok) szakaszt.

### Több állomás figyelése
Az alkalmazás állomásonként egy példányt futtat. Nem kell hozzányúlni a Python
kódhoz: vegyél fel az `apps.yaml`-ba még egy blokkot **másik legfelső szintű
névvel**, és add meg benne a másik állomás `allomas_voa` kódját és a saját
entity ID-jait.

```yaml
HydrologyData_agard:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "1649619E-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.agard_water_level
  water_level_friendly_name: "Agárd Water Level"
  water_temperature_entity: sensor.agard_water_temperature
  water_temperature_friendly_name: "Agárd Water Temperature"

HydrologyData_balatonfured:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "164961AD-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.balatonfured_water_level
  water_level_friendly_name: "Balatonfüred Water Level"
  water_temperature_entity: sensor.balatonfured_water_temperature
  water_temperature_friendly_name: "Balatonfüred Water Temperature"
```

Amire figyelj:

- A legfelső szintű név (`HydrologyData_agard`) tetszőleges, de **egyedi** kell
  legyen. A `class` és a `module` minden blokkban ugyanaz marad.
- Az `entity` értékek is legyenek egyediek, különben a példányok felülírják
  egymás szenzorait.
- Minden példány önállóan, óránként kérdezi le a saját állomását.

### Az állomás `allomas_voa` kódjának megkeresése
A VOA kód egy GUID, amit a vizugy.hu sehol nem ír ki szövegesen. Három módon
juthatsz hozzá.

**A mellékelt listából:** a [STATIONS.md](STATIONS.md) tartalmazza mind a ~860
állomást a kódjával együtt. Nem kell hozzá se hálózat, se szkript, elég
rákeresni a névre. Pillanatkép, a lista újragenerálható a szkripttel.

**A böngészőből:** nyisd meg az
[Operatív grafikon](https://www.vizugy.hu/?mapModule=OpGrafikon&mapData=Idosor)
oldalt, válaszd ki a vízmércét a legördülő listából, és a címsorban megjelenő
`AllomasVOA=...` érték lesz a kód.

**A mellékelt szkripttel:** a `list_stations.py` letölti ugyanezt a listát és
kikeresi belőle az állomást. Az ékezeteket és a kis/nagybetűt figyelmen kívül
hagyja.

```bash
python list_stations.py agard
# 1649619E-97AB-11D4-BB62-00508BA24287  Agárd (818   )

python list_stations.py --yaml balatonfured
# kiírja a fenti formátumú, beilleszthető apps.yaml blokkot
```

Kapcsoló nélkül mind a ~860 állomást kilistázza.

### Ismert korlátok
- **Nem minden állomás mér vízhőmérsékletet.** Ahol nincs adat, ott a
  vízállás szenzor létrejön, a hőmérséklet szenzor nem. Ez nem hiba.
- Az alkalmazás elsődlegesen a *felszín közeli* vízhőt olvassa. Ha az adott
  állomás csak *mederfenék közeli* értéket közöl (például Balatonfüred),
  akkor azt használja, és ezt a naplóba is kiírja.
- **A vizugy.hu hiányos tanúsítványláncot küld.** A kiszolgált köztes
  tanúsítvány (`e-Szigno OV TLS CA 2026`) nem az, amelyik a szervertanúsítványt
  aláírta (`e-Szigno RSA OV TLS CA 2026`). A böngésző a hiányzót AIA-ból
  magától letölti, az OpenSSL nem, ezért a Python `SSLError`-ral eleshet.

  Az alkalmazásnak ehhez két kapcsolója van az `apps.yaml`-ban:

  - `verify_ssl` (alapértelmezés: `true`) — a tanúsítvány ellenőrzése.
  - `allow_insecure_ssl_fallback` (alapértelmezés: `false`) — `SSLError`
    esetén egyszer újrapróbálja ellenőrzés nélkül. Naplózza, de **gyengíti a
    TLS védelmet**, ezért csak átmeneti megoldásnak érdemes bekapcsolni.

  A `list_stations.py` ugyanezt a helyzetet `--ca-bundle` kapcsolóval kezeli.
  Ha a láncot inkább kipótolnád, mint hogy kikapcsold az ellenőrzést:

  ```bash
  curl -o ca.crt http://ovtlsca2026-ca.e-szigno.hu/ovtlsca2026.crt
  openssl x509 -inform DER -in ca.crt -out ca.pem
  cat "$(python -c 'import certifi; print(certifi.where())')" ca.pem > bundle.pem
  python list_stations.py --ca-bundle bundle.pem agard
  ```

### Telepítési lépések
1. Mentsd el a Python szkriptet `hydroinfo.py` néven az AppDaemon `apps` könyvtárába.
2. Frissítsd az `apps.yaml` fájlt a fenti módon.
3. Indítsd újra az AppDaemont a változtatások alkalmazásához.
4. Ellenőrizd a naplókat, hogy az adatok sikeresen lekérhetők és a szenzorok létrejönnek-e a Home Assistantban.

### Létrehozott szenzorok
A szenzorok entity ID-ja és megjelenített neve a YAML konfigurációban megadott értékekből jön.

1. **`sensor.agard_water_level`**:
   - A vízállás értéket cm-ben jeleníti meg.
   - Attribútumok:
     - `state_class`: `measurement`
     - `last_changed`: A mérés időpontja.
     - `friendly_name`: `Agárd Water Level`

2. **`sensor.agard_water_temperature`**:
   - A vízhőmérséklet értéket °C-ban jeleníti meg.
   - Attribútumok:
     - `state_class`: `measurement`
     - `last_changed`: A mérés időpontja.
     - `friendly_name`: `Agárd Water Temperature`

### Naplók
Az AppDaemon naplóiban ellenőrizheted az adatok lekérését és a szenzorok frissítését:
- A sikeres frissítések naplózzák a lekért értékeket és a szenzor állapotokat.
- A hibák a nem érvényes adatokra vagy kapcsolat problémákra vonatkozó üzeneteket tartalmaznak.

---

### Overview
HydrologyData is an AppDaemon app designed to fetch and process hydrological data from the Hungarian Water Management Authority's website. The app extracts data such as water level (cm) and water temperature (°C) and creates corresponding sensors in Home Assistant.

### Requirements
1. AppDaemon installed and configured.
2. Python libraries:
   - `requests`
   - `bs4` (BeautifulSoup4)
   - `fake_useragent`

### Configuration
Add the following configuration to your `apps.yaml` file:

```yaml
HydrologyData:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "1649619E-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.agard_water_level
  water_level_friendly_name: "Agárd Water Level"
  water_temperature_entity: sensor.agard_water_temperature
  water_temperature_friendly_name: "Agárd Water Temperature"
```

- **`class`**: The name of the class in the script.
- **`module`**: The name of the Python module (file without `.py` extension).
- **`allomas_voa`**: The station identifier (VOA code) for fetching data.
- **`water_level_entity`**: The Home Assistant entity ID for the water level sensor.
- **`water_level_friendly_name`**: The display name for the water level sensor.
- **`water_temperature_entity`**: The Home Assistant entity ID for the water temperature sensor.
- **`water_temperature_friendly_name`**: The display name for the water temperature sensor.
- **`verify_ssl`** *(optional, default `true`)*: whether the vizugy.hu certificate is verified.
- **`allow_insecure_ssl_fallback`** *(optional, default `false`)*: retry once without verification after an `SSLError`. See [Known Limitations](#known-limitations).

### Monitoring More Than One Station
The app runs one instance per station. No code change is needed: add another
block to `apps.yaml` under a **different top-level name**, with that station's
`allomas_voa` and its own entity IDs.

```yaml
HydrologyData_agard:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "1649619E-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.agard_water_level
  water_level_friendly_name: "Agárd Water Level"
  water_temperature_entity: sensor.agard_water_temperature
  water_temperature_friendly_name: "Agárd Water Temperature"

HydrologyData_balatonfured:
  class: HydrologyData
  module: hydroinfo
  allomas_voa: "164961AD-97AB-11D4-BB62-00508BA24287"
  water_level_entity: sensor.balatonfured_water_level
  water_level_friendly_name: "Balatonfüred Water Level"
  water_temperature_entity: sensor.balatonfured_water_temperature
  water_temperature_friendly_name: "Balatonfüred Water Temperature"
```

Things to watch for:

- The top-level name (`HydrologyData_agard`) is free-form but must be
  **unique**. `class` and `module` stay the same in every block.
- The entity IDs must be unique too, otherwise the instances overwrite each
  other's sensors.
- Each instance polls its own station once per hour, independently.

### Finding the `allomas_voa` of a Station
The VOA code is a GUID that vizugy.hu never shows as text. There are three
ways to get it.

**From the bundled list:** [STATIONS.md](STATIONS.md) contains all ~860
stations with their codes. No network access and no script needed, just search
for the name. It is a snapshot and can be regenerated with the script.

**From the browser:** open the
[operational chart page](https://www.vizugy.hu/?mapModule=OpGrafikon&mapData=Idosor),
pick the gauge from the dropdown, and read the `AllomasVOA=...` value from the
address bar.

**With the bundled script:** `list_stations.py` downloads the same list and
searches it. Matching ignores case and accents.

```bash
python list_stations.py agard
# 1649619E-97AB-11D4-BB62-00508BA24287  Agárd (818   )

python list_stations.py --yaml balatonfured
# prints a ready to paste apps.yaml block in the format shown above
```

Without arguments it lists all ~860 stations.

### Known Limitations
- **Not every station measures water temperature.** Where there is no reading
  the water level sensor is still created, the temperature sensor is not.
  This is expected.
- The app prefers the *near surface* water temperature. When a station only
  publishes a *near river bed* value (Balatonfüred, for example) that reading
  is used instead, and the fallback is written to the log.
- **vizugy.hu serves an incomplete certificate chain.** The intermediate it
  sends (`e-Szigno OV TLS CA 2026`) is not the one that signed the server
  certificate (`e-Szigno RSA OV TLS CA 2026`). Browsers fetch the missing one
  over AIA, OpenSSL does not, so Python can fail with `SSLError`.

  The app has two options for this in `apps.yaml`:

  - `verify_ssl` (default `true`) — whether the certificate is verified.
  - `allow_insecure_ssl_fallback` (default `false`) — retry once without
    verification after an `SSLError`. It is logged, but it **weakens TLS**,
    so treat it as a temporary measure.

  `list_stations.py` handles the same situation with `--ca-bundle`. To repair
  the chain instead of turning verification off:

  ```bash
  curl -o ca.crt http://ovtlsca2026-ca.e-szigno.hu/ovtlsca2026.crt
  openssl x509 -inform DER -in ca.crt -out ca.pem
  cat "$(python -c 'import certifi; print(certifi.where())')" ca.pem > bundle.pem
  python list_stations.py --ca-bundle bundle.pem agard
  ```

### Deployment Steps
1. Save the Python script as `hydroinfo.py` in your AppDaemon `apps` directory.
2. Update the `apps.yaml` file as shown above.
3. Restart AppDaemon to apply changes.
4. Verify the logs to ensure data is being fetched and sensors are created in Home Assistant.

### Sensors Created
The sensor entity IDs and display names come from the values configured in YAML.

1. **`sensor.agard_water_level`**:
   - Represents the water level in cm.
   - Attributes:
     - `state_class`: `measurement`
     - `last_changed`: Timestamp of the measurement.
     - `friendly_name`: `Agárd Water Level`

2. **`sensor.agard_water_temperature`**:
   - Represents the water temperature in °C.
   - Attributes:
     - `state_class`: `measurement`
     - `last_changed`: Timestamp of the measurement.
     - `friendly_name`: `Agárd Water Temperature`

### Logs
Check the AppDaemon logs to confirm data fetching and sensor updates:
- Successful updates log the fetched values and sensor states.
- Errors are logged for invalid data or connection issues.
