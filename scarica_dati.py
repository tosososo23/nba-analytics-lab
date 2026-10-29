
from pathlib import Path
import time
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog

CARTELLA = Path(__file__).parent
STAGIONI = ["2025-26", "2026-27"]


def scarica(tipo, stagione):
    print(f"Scarico {tipo}, stagione {stagione}...")
    dati = leaguegamelog.LeagueGameLog(
        player_or_team_abbreviation=tipo,
        season=stagione,
        season_type_all_star="Regular Season",
        timeout=90,
    ).get_data_frames()[0]

    if not dati.empty:
        dati["SEASON"] = stagione

    print(f"Righe ricevute: {len(dati)}")
    return dati


def aggiorna(nome_file, nuovi, tipo):
    percorso = CARTELLA / nome_file

    if nuovi.empty:
        print(f"Nessun dato nuovo per {nome_file}.")
        return

    if percorso.exists():
        vecchi = pd.read_csv(percorso, low_memory=False)
        dati = pd.concat([vecchi, nuovi], ignore_index=True, sort=False)
    else:
        dati = nuovi.copy()

    chiavi = (
        ["GAME_ID", "PLAYER_ID"]
        if tipo == "P"
        else ["GAME_ID", "TEAM_ID"]
    )

    dati = dati.drop_duplicates(subset=chiavi, keep="last")

    temporaneo = percorso.with_suffix(".tmp")
    dati.to_csv(temporaneo, index=False, encoding="utf-8-sig")
    temporaneo.replace(percorso)

    print(f"{nome_file}: {len(dati)} righe totali salvate.")


def main():
    # Backup iniziale: non sovrascrive eventuali copie precedenti.
    for nome in ["player_games.csv", "team_games.csv"]:
        originale = CARTELLA / nome
        backup = CARTELLA / (nome + ".backup")

        if originale.exists() and not backup.exists():
            backup.write_bytes(originale.read_bytes())
            print(f"Backup creato: {backup.name}")

    giocatori = []
    squadre = []

    for stagione in STAGIONI:
        for tipo, raccolta in [("P", giocatori), ("T", squadre)]:
            try:
                dati = scarica(tipo, stagione)
                if not dati.empty:
                    raccolta.append(dati)
            except Exception as errore:
                print(f"Errore per {tipo}, {stagione}: {errore}")

            time.sleep(2)

    if giocatori:
        aggiorna(
            "player_games.csv",
            pd.concat(giocatori, ignore_index=True),
            "P",
        )

    if squadre:
        aggiorna(
            "team_games.csv",
            pd.concat(squadre, ignore_index=True),
            "T",
        )

    print("Download terminato. Controlla eventuali errori.")


if __name__ == "__main__":
    main()
