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
```

- **`class`**: Az osztály neve a szkriptben.
- **`module`**: A Python modul neve (fájl `.py` kiterjesztés nélkül).
- **`allomas_voa`**: Az állomás azonosítója (VOA kód) az adatok lekéréséhez.

### Telepítési lépések
1. Mentsd el a Python szkriptet `hydroinfo.py` néven az AppDaemon `apps` könyvtárába.
2. Frissítsd az `apps.yaml` fájlt a fenti módon.
3. Indítsd újra az AppDaemont a változtatások alkalmazásához.
4. Ellenőrizd a naplókat, hogy az adatok sikeresen lekérhetők és a szenzorok létrejönnek-e a Home Assistantban.

### Létrehozott szenzorok
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
```

- **`class`**: The name of the class in the script.
- **`module`**: The name of the Python module (file without `.py` extension).
- **`allomas_voa`**: The station identifier (VOA code) for fetching data.

### Deployment Steps
1. Save the Python script as `hydroinfo.py` in your AppDaemon `apps` directory.
2. Update the `apps.yaml` file as shown above.
3. Restart AppDaemon to apply changes.
4. Verify the logs to ensure data is being fetched and sensors are created in Home Assistant.

### Sensors Created
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
