#!/usr/bin/env python3
"""
Modularisierte Pipeline: Nachrichten-Impact auf den Dow Jones
--------------------------------------------------------------

Dieses Skript führt folgende Aufgaben aus:
  1. Abruf mehrerer RSS-Feeds, um Nachrichten zu sammeln.
  2. Vermeidung von doppelten Einträgen mittels eines Hash-Logs.
  3. Besuch der zugehörigen Links und Extraktion des Website-Textinhalts.
  4. Speicherung des extrahierten Inhalts in einer Textdatei (mit Zeitstempel und Titel).
  5. Aufbau eines DataFrames, das Datum, Titel, Link, Quelle, Hash und Dateinamen enthält.
  6. Abruf von Dow Jones-Kursdaten (Ticker "^DJI") und Einordnung der Reaktion.
  7. Speicherung des finalen DataFrames als CSV.
  8. (Optional) Erzeugung eines explorativen HTML-Reports mit pandas_profiling.

Die Pipeline wurde so moduliert, dass jeder Schritt in einer eigenen Funktion implementiert ist. 
Dadurch ist der Code übersichtlich, gut wartbar und leicht erweiterbar.

Autor: Dein Name  
Datum: YYYY-MM-DD
"""

import os
import hashlib
from datetime import datetime
from urllib.parse import urljoin

import feedparser        # RSS-Feeds abrufen
import requests          # HTTP-Anfragen
from bs4 import BeautifulSoup  # HTML parsen
import pandas as pd      # Datenhandling
import yfinance as yf    # Börsendaten

# Optional: pandas_profiling für den explorativen Report
try:
    from pandas_profiling import ProfileReport
    HAS_PROFILING = True
except ImportError:
    HAS_PROFILING = False


# ----------------------------------------------------------------------
# Hilfsfunktionen zur Verwaltung von Hashes (zum Verhindern doppelter Einträge)
# ----------------------------------------------------------------------
LOG_FILE = 'processed_hashes.csv'

def compute_hash(entry):
    """
    Berechnet einen MD5-Hash eines RSS-Eintrags anhand von published, title und link.
    
    Parameter:
      entry (dict): Ein RSS-Eintrag.
      
    Rückgabe:
      str: Der berechnete Hash.
    """
    data = entry.get('published', '') + entry.get('title', '') + entry.get('link', '')
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def load_processed_hashes(log_file):
    """
    Lädt die bereits verarbeiteten Hash-Werte aus einer CSV-Datei.
    
    Parameter:
      log_file (str): Dateiname der Log-Datei.
      
    Rückgabe:
      set: Menge der verarbeiteten Hashes.
    """
    if os.path.exists(log_file):
        df_hash = pd.read_csv(log_file)
        return set(df_hash['hash'])
    return set()

def save_processed_hashes(processed_hashes, log_file):
    """
    Speichert die verarbeiteten Hashes in einer CSV-Datei.
    
    Parameter:
      processed_hashes (set): Menge der Hash-Werte.
      log_file (str): Dateiname, in den geschrieben werden soll.
    """
    df_hash = pd.DataFrame({'hash': list(processed_hashes)})
    df_hash.to_csv(log_file, index=False)


# ----------------------------------------------------------------------
# Funktion: Website-Inhalt abrufen und in eine Textdatei speichern
# ----------------------------------------------------------------------
def scrape_entry_content(link, title, timeout=10):
    """
    Ruft den Inhalt einer Website ab und speichert ihn in einer Textdatei.
    
    Parameter:
      link (str): URL der Website.
      title (str): Titel des Eintrags (wird zur Dateibenennung genutzt).
      timeout (int): Timeout für die HTTP-Anfrage.
      
    Rückgabe:
      str: Der erstellte Dateiname oder ein leerer String bei Fehlern.
    """
    try:
        response = requests.get(link, timeout=timeout)
        if response.status_code == 200:
            # Parse den HTML-Inhalt mit BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            # Extrahiere den reinen Text, wobei newline-Separators die Struktur erhalten
            content = soup.get_text(separator="\n", strip=True)
            # Erzeuge einen sicheren Dateinamen: aktueller Zeitstempel + "bereinigter" Titel (max. 50 Zeichen)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_")).rstrip()
            filename = f"{timestamp}_{safe_title[:50]}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            return filename
        else:
            print(f"Warnung: Abruf von {link} ergab Statuscode {response.status_code}.")
    except Exception as e:
        print(f"Fehler beim Abruf von {link}: {e}")
    return ""


# ----------------------------------------------------------------------
# Funktion: Verarbeitung der RSS-Feeds
# ----------------------------------------------------------------------
def process_feeds(feeds, processed_hashes):
    """
    Verarbeitet eine Liste von RSS-Feeds, extrahiert alle neuen Einträge (ohne Duplikate)
    und ruft die zugehörigen Inhalte ab.
    
    Parameter:
      feeds (list): Liste von Feed-URLs.
      processed_hashes (set): bereits verarbeitete Hash-Werte.
      
    Rückgabe:
      list: Liste von Dictionaries mit den Eintragsdaten.
    """
    entries_list = []
    
    print("Beginne mit der Verarbeitung der RSS-Feeds ...")
    for feed_url in feeds:
        print("Verarbeite Feed:", feed_url)
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            entry_hash = compute_hash(entry)
            if entry_hash in processed_hashes:
                # Überspringe bereits verarbeitete Einträge
                continue
            # Markiere diesen Eintrag als verarbeitet
            processed_hashes.add(entry_hash)
            
            entry_date = entry.get('published', '')
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            source = feed_url  # Nutze die Feed-URL als Quelle
            # Rufe den Website-Inhalt ab und speichere ihn
            file_name = scrape_entry_content(link, title)
            
            entries_list.append({
                "Datum": entry_date,
                "Titel": title,
                "Kurzbeschreibung": summary,
                "Link": link,
                "Quelle": source,
                "hash": entry_hash,
                "Dateiname": file_name
            })
    print("RSS-Feeds Verarbeitung abgeschlossen.")
    return entries_list


# ----------------------------------------------------------------------
# Funktion: Abruf der Dow Jones-Daten und Bestimmung der Reaktion
# ----------------------------------------------------------------------
def retrieve_dow_reaction():
    """
    Ruft die letzten zwei Tage der Dow Jones-Kursdaten ab und vergleicht den Schlusskurs.
    
    Rückgabe:
      str: "höher", "tiefer", "gleich" oder "unbekannt"
    """
    print("Lade Dow Jones Daten ...")
    dow = yf.Ticker("^DJI")
    # Abrufen der letzten 2 Tage; ausreichend für den Vergleich
    history = dow.history(period="2d")
    if len(history) >= 2:
        prev_close = history['Close'].iloc[-2]
        current_close = history['Close'].iloc[-1]
        if current_close > prev_close:
            return "höher"
        elif current_close < prev_close:
            return "tiefer"
        else:
            return "gleich"
    else:
        return "unbekannt"


# ----------------------------------------------------------------------
# Funktion: Erzeugung eines explorativen Reports (optional)
# ----------------------------------------------------------------------
def generate_exploratory_report(df, report_file="news_dow_study_report.html"):
    """
    Erzeugt einen explorativen Report mithilfe von pandas_profiling und speichert diesen als HTML.
    
    Parameter:
      df (DataFrame): Das DataFrame mit den gesammelten Daten.
      report_file (str): Dateiname des Reports.
    """
    if HAS_PROFILING:
        print("Erstelle explorativen Report ...")
        profile = ProfileReport(df, title="News Dow Study Report", explorative=True)
        profile.to_file(report_file)
        print("Explorationsreport erstellt als:", report_file)
    else:
        print("pandas_profiling ist nicht installiert. Überspringe Report-Erstellung.")


# ----------------------------------------------------------------------
# Main-Pipeline: Orchestrierung aller Schritte
# ----------------------------------------------------------------------
def main():
    """
    Hauptfunktion, die die gesamte Pipeline ausführt.
    """
    # 1. Lade bereits verarbeitete Hashes, um doppelte Einträge zu vermeiden
    processed_hashes = load_processed_hashes(LOG_FILE)
    
    # 2. Definiere die Liste der RSS-Feeds (hier können beliebig weitere hinzugefügt werden)
    feeds = [
        "https://www.tagesschau.de/xml/rss2",
        "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",
        "https://www.spiegel.de/schlagzeilen/tops/index.rss"
    ]
    
    # 3. Verarbeite alle Feeds und erhalte neue Einträge
    entries = process_feeds(feeds, processed_hashes)
    
    # 4. Erstelle ein DataFrame mit den gesammelten Einträgen
    df = pd.DataFrame(entries)
    
    # 5. Abruf der Dow Jones-Daten und Bestimme die Reaktion (höher, tiefer, gleich)
    dow_reaction = retrieve_dow_reaction()
    df['Dow_Reaktion'] = dow_reaction
    
    # 6. Speichere das finale DataFrame als CSV-Datei
    output_csv = "news_dow_study.csv"
    df.to_csv(output_csv, index=False)
    print("Finales DataFrame gespeichert in:", output_csv)
    
    # 7. Speichere die verarbeiteten Hashes in der Log-Datei
    save_processed_hashes(processed_hashes, LOG_FILE)
    
    # 8. Optional: Erzeuge einen explorativen Report als HTML (falls pandas_profiling installiert ist)
    generate_exploratory_report(df)
    

# ----------------------------------------------------------------------
# Einstiegspunkt des Skripts
# ----------------------------------------------------------------------
if __name__ == '__main__':
    main()