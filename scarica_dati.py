

from pathlib import Path
import sys
import time
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog
from curl_cffi import requests as curl_requests
from nba_api.stats.library.http import NBAStatsHTTP

SESSIONE_NBA = curl_requests.Session(impersonate="chrome")

NBAStatsHTTP.get_session = lambda self: SESSIONE_NBA


CARTELLA = Path(__file__).parent
STAGIONI = ["2025-26", "2026-27"]
TENTATIVI = 3
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

def scarica(tipo, stagione):
    ultimo_errore = None

    for tentativo in range(1, TENTATIVI + 1):
        try:
            print(
                f"Scarico {tipo}, stagione {stagione} "
                f"(tentativo {tentativo}/{TENTATIVI})...",
                flush=True,
            )

            dati = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation=tipo,
                season=stagione,
                season_type_all_star="Regular Season",
                headers=HEADERS,
                timeout=120,
            ).get_data_frames()[0]

            if not dati.empty:
                dati["SEASON"] = stagione

            print(f"Righe ricevute: {len(dati)}", flush=True)
            return dati

        except Exception as errore:
            ultimo_errore = errore
            print(f"Richiesta fallita: {errore}", flush=True)

            if tentativo < TENTATIVI:
                pausa = tentativo * 15
                print(f"Nuovo tentativo tra {pausa} secondi...")
                time.sleep(pausa)

    raise RuntimeError(
        f"Download fallito per {tipo}, stagione {stagione} "
        f"dopo {TENTATIVI} tentativi: {ultimo_errore}"
    )


def aggiorna(nome_file, nuovi, tipo):
    percorso = CARTELLA / nome_file

    if nuovi.empty:
        raise RuntimeError(f"Nessun dato ricevuto per {nome_file}.")

    if percorso.exists():
        vecchi = pd.read_csv(percorso, low_memory=False)
        dati = pd.concat(
            [vecchi, nuovi],
            ignore_index=True,
            sort=False,
        )
    else:
        dati = nuovi.copy()

    chiavi = (
        ["GAME_ID", "PLAYER_ID"]
        if tipo == "P"
        else ["GAME_ID", "TEAM_ID"]
    )

    dati = dati.drop_duplicates(subset=chiavi, keep="last")

    temporaneo = percorso.with_suffix(".tmp")
    try:
        dati.to_csv(temporaneo, index=False, encoding="utf-8-sig")
        temporaneo.replace(percorso)
    finally:
        if temporaneo.exists():
            temporaneo.unlink()

    print(f"{nome_file}: {len(dati)} righe totali salvate.")


def main():
    giocatori = []
    squadre = []
    errori = []

    for stagione in STAGIONI:
        for tipo, raccolta in [("P", giocatori), ("T", squadre)]:
            try:
                dati = scarica(tipo, stagione)

                if dati.empty:
                    raise RuntimeError(
                        f"Nessun dato restituito per {tipo}, {stagione}"
                    )

                raccolta.append(dati)

            except Exception as errore:
                messaggio = f"{tipo}, {stagione}: {errore}"
                errori.append(messaggio)
                print(f"ERRORE: {messaggio}", flush=True)

            time.sleep(5)

    # Non aggiornare i CSV se anche una sola richiesta è fallita.
    # In questo modo un download parziale non viene pubblicato.
    if errori:
        print(
            "\nAggiornamento annullato. I CSV esistenti "
            "non sono stati modificati."
        )
        for errore in errori:
            print(f"- {errore}")
        sys.exit(1)

    if not giocatori or not squadre:
        print("Errore: mancano dati per giocatori o squadre.")
        sys.exit(1)

    aggiorna(
        "player_games.csv",
        pd.concat(giocatori, ignore_index=True),
        "P",
    )

    aggiorna(
        "team_games.csv",
        pd.concat(squadre, ignore_index=True),
        "T",
    )

    print("Download e aggiornamento completati.", flush=True)


if __name__ == "__main__":
    main()

