#!/usr/bin/env python3
"""List the water gauge stations published by vizugy.hu.

The AppDaemon app needs the ``allomas_voa`` identifier of a station. That
identifier is not shown anywhere on the website, it only appears in the
station selector of the "Operatív grafikon" page. This helper downloads that
selector and prints the stations together with their identifier, so a new
station can be added to ``apps.yaml`` without digging through the page source.

Usage:
    python list_stations.py                  # every station
    python list_stations.py agard            # stations matching "agard"
    python list_stations.py --yaml agard     # ready to paste apps.yaml block

Matching ignores case and accents, so "agard" finds "Agárd".

vizugy.hu does not always serve the intermediate certificate that signed its
TLS certificate. Browsers download the missing certificate automatically,
OpenSSL does not, so Python may reject the connection. If that happens, pass
the missing certificate with --ca-bundle; see the README for details.
"""

import argparse
import re
import sys
import unicodedata

import requests
from bs4 import BeautifulSoup

STATION_LIST_URL = "https://www.vizugy.hu/?mapModule=OpGrafikon&mapData=Idosor"
SELECT_NAME = "vizmercevalaszto"
REQUEST_TIMEOUT = 30


def strip_accents(text):
    """Return ``text`` without diacritics, for accent insensitive matching."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def slugify(name):
    """Turn a station name into something usable inside an entity id."""
    base = strip_accents(name).lower()
    base = re.sub(r"\(.*?\)", " ", base)
    base = re.sub(r"[^a-z0-9]+", "_", base)
    return base.strip("_") or "station"


def fetch_stations(ca_bundle=None):
    """Download the station selector and return a list of (voa, name) pairs."""
    response = requests.get(
        STATION_LIST_URL, timeout=REQUEST_TIMEOUT, verify=ca_bundle or True
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    select = soup.find("select", attrs={"name": SELECT_NAME})
    if select is None:
        raise RuntimeError(
            "The '%s' selector was not found. The page layout may have changed."
            % SELECT_NAME
        )

    stations = []
    for option in select.find_all("option"):
        voa = (option.get("value") or "").strip()
        name = option.get_text(strip=True)
        if voa and name:
            stations.append((voa, name))
    return stations


def filter_stations(stations, query):
    if not query:
        return stations
    needle = strip_accents(query).lower()
    return [(voa, name) for voa, name in stations
            if needle in strip_accents(name).lower()]


def print_table(stations):
    for voa, name in stations:
        print("%s  %s" % (voa, name))
    print("\n%d station(s)" % len(stations), file=sys.stderr)


def print_markdown(stations):
    print("| Station | `allomas_voa` |")
    print("| --- | --- |")
    for voa, name in stations:
        print("| %s | `%s` |" % (name.replace("|", "\\|"), voa))


def print_yaml(stations):
    for voa, name in stations:
        slug = slugify(name)
        display = name.split("(")[0].strip()
        print("HydrologyData_%s:" % slug)
        print("  class: HydrologyData")
        print("  module: hydroinfo")
        print('  allomas_voa: "%s"' % voa)
        print("  water_level_entity: sensor.%s_water_level" % slug)
        print('  water_level_friendly_name: "%s Water Level"' % display)
        print("  water_temperature_entity: sensor.%s_water_temperature" % slug)
        print('  water_temperature_friendly_name: "%s Water Temperature"' % display)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="List vizugy.hu water gauge stations and their allomas_voa."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="only show stations whose name contains this text "
             "(case and accent insensitive)",
    )
    parser.add_argument(
        "--yaml",
        action="store_true",
        help="print an apps.yaml block for each matching station",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="print the stations as a Markdown table, used to regenerate "
             "STATIONS.md",
    )
    parser.add_argument(
        "--ca-bundle",
        metavar="PATH",
        help="CA bundle to verify vizugy.hu with, needed when the site does "
             "not serve its intermediate certificate",
    )
    args = parser.parse_args()

    try:
        stations = fetch_stations(args.ca_bundle)
    except requests.exceptions.SSLError as err:
        print("TLS verification against vizugy.hu failed: %s" % err,
              file=sys.stderr)
        print("The site may be serving an incomplete certificate chain. "
              "See the README for how to build a CA bundle and pass it with "
              "--ca-bundle.", file=sys.stderr)
        return 1
    except (requests.RequestException, RuntimeError) as err:
        print("Failed to download the station list: %s" % err, file=sys.stderr)
        return 1

    matches = filter_stations(stations, args.query)
    if not matches:
        print("No station matches %r." % args.query, file=sys.stderr)
        return 1

    if args.yaml:
        print_yaml(matches)
    elif args.markdown:
        print_markdown(matches)
    else:
        print_table(matches)
    return 0


if __name__ == "__main__":
    sys.exit(main())
