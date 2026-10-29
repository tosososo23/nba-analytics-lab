
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------
# NBA ANALYTICS LAB
# --------------------------------------------------

CARTELLA = Path(__file__).parent

st.set_page_config(
    page_title="NBA Analytics Lab",
    page_icon="🏀",
    layout="wide",
)

st.title("🏀 NBA ANALYTICS LAB")
st.caption("Statistiche NBA | Giocatori | Squadre | Previsioni")

# --------------------------------------------------
# CARICAMENTO DATI
# --------------------------------------------------

@st.cache_data
def carica_csv(nome_file):
    percorso = CARTELLA / nome_file

    if not percorso.exists():
        return pd.DataFrame()

    return pd.read_csv(percorso, low_memory=False)


giocatori = carica_csv("player_games.csv")
squadre = carica_csv("team_games.csv")

if giocatori.empty or squadre.empty:
    st.error(
        "Non trovo i dati oppure i file sono vuoti. "
        "Controlla che player_games.csv e team_games.csv "
        "siano nella stessa cartella di app.py."
    )
    st.stop()

# Converte le colonne numeriche, se necessario.
for colonna in ["PTS", "REB", "AST", "STL", "BLK", "MIN"]:
    if colonna in giocatori.columns:
        giocatori[colonna] = pd.to_numeric(
            giocatori[colonna], errors="coerce"
        )

for colonna in ["PTS", "REB", "AST"]:
    if colonna in squadre.columns:
        squadre[colonna] = pd.to_numeric(
            squadre[colonna], errors="coerce"
        )

st.success(
    f"Dati caricati correttamente: "
    f"{len(giocatori):,} righe giocatore e "
    f"{len(squadre):,} righe squadra."
)

# --------------------------------------------------
# FILTRO STAGIONE
# --------------------------------------------------

if "SEASON" in giocatori.columns:
    stagioni = sorted(
        giocatori["SEASON"].dropna().astype(str).unique()
    )
    stagione_scelta = st.sidebar.selectbox(
        "Stagione NBA",
        ["Tutte"] + stagioni,
    )
else:
    stagione_scelta = "Tutte"

if stagione_scelta != "Tutte" and "SEASON" in giocatori.columns:
    giocatori_filtrati = giocatori[
        giocatori["SEASON"].astype(str) == stagione_scelta
    ].copy()
else:
    giocatori_filtrati = giocatori.copy()

# --------------------------------------------------
# SCHEDE PRINCIPALI
# --------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🏀 Giocatori",
        "🏆 Squadre",
        "📈 Previsioni",
        "📋 Dati e classifiche",
    ]
)

# ==================================================
# TAB 1 - GIOCATORI
# ==================================================

with tab1:
    st.header("Statistiche giocatori")

    if "PLAYER_NAME" not in giocatori_filtrati.columns:
        st.error("Manca la colonna PLAYER_NAME nel CSV.")
    else:
        nomi = sorted(
            giocatori_filtrati["PLAYER_NAME"]
            .dropna().unique().tolist()
        )

        if not nomi:
            st.warning("Nessun giocatore disponibile.")
        else:
            nome = st.selectbox("Scegli un giocatore", nomi)

            storico = giocatori_filtrati[
                giocatori_filtrati["PLAYER_NAME"] == nome
            ].copy()

            if "GAME_DATE" in storico.columns:
                storico["GAME_DATE"] = pd.to_datetime(
                    storico["GAME_DATE"], errors="coerce"
                )
                storico = storico.sort_values("GAME_DATE")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Punti medi",
                f"{storico['PTS'].mean():.1f}"
                if "PTS" in storico.columns else "N/D"
            )
            c2.metric(
                "Rimbalzi medi",
                f"{storico['REB'].mean():.1f}"
                if "REB" in storico.columns else "N/D"
            )
            c3.metric(
                "Assist medi",
                f"{storico['AST'].mean():.1f}"
                if "AST" in storico.columns else "N/D"
            )
            c4.metric("Partite", len(storico))

            statistiche = [
                c for c in ["PTS", "REB", "AST", "STL", "BLK"]
                if c in storico.columns
            ]

            if statistiche:
                statistica = st.selectbox(
                    "Statistica da visualizzare",
                    statistiche,
                )

                if "GAME_DATE" in storico.columns:
                    grafico = storico.dropna(
                        subset=["GAME_DATE", statistica]
                    ).set_index("GAME_DATE")[[statistica]]

                    st.line_chart(grafico)

            colonne = [
                c for c in [
                    "GAME_DATE", "MATCHUP", "WL", "MIN",
                    "PTS", "REB", "AST", "STL", "BLK",
                ]
                if c in storico.columns
            ]

            # COSTANZA E RENDIMENTO DEL GIOCATORE
            # ANALISI DEI TIRI
            st.subheader("🎯 Analisi dei tiri")

            colonne_tiro = [
                "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"
            ]

            mancanti = [
                c for c in colonne_tiro
                if c not in storico.columns
            ]

            if mancanti:
                st.warning(
                    "Nel dataset mancano queste colonne: "
                    + ", ".join(mancanti)
                    + ". Non possiamo calcolare tutte le percentuali."
                )
            else:
                fgm = pd.to_numeric(
                    storico["FGM"], errors="coerce"
                ).sum()
                fga = pd.to_numeric(
                    storico["FGA"], errors="coerce"
                ).sum()
                fg3m = pd.to_numeric(
                    storico["FG3M"], errors="coerce"
                ).sum()
                fg3a = pd.to_numeric(
                    storico["FG3A"], errors="coerce"
                ).sum()
                ftm = pd.to_numeric(
                    storico["FTM"], errors="coerce"
                ).sum()
                fta = pd.to_numeric(
                    storico["FTA"], errors="coerce"
                ).sum()

                def pct_tiro(realizzati, tentati):
                    if tentati <= 0:
                        return "N/D"
                    return f"{100 * realizzati / tentati:.1f}%"

                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Tiri dal campo (FG)",
                    f"{fgm:.0f}/{fga:.0f}"
                )
                c2.metric(
                    "Triple",
                    f"{fg3m:.0f}/{fg3a:.0f}"
                )
                c3.metric(
                    "Tiri liberi",
                    f"{ftm:.0f}/{fta:.0f}"
                )

                c1, c2, c3 = st.columns(3)
                c1.metric("FG%", pct_tiro(fgm, fga))
                c2.metric("3P%", pct_tiro(fg3m, fg3a))
                c3.metric("FT%", pct_tiro(ftm, fta))

                st.caption(
                    "Realizzati/tentati e percentuali calcolati "
                    "sulle partite del giocatore attualmente selezionato."
                )

            st.subheader("Costanza e rendimento")

            if "PTS" in storico.columns:
                punti = pd.to_numeric(
                    storico["PTS"], errors="coerce"
                ).dropna()

                if not punti.empty:
                    ultime5 = punti.tail(5)
                    ultime10 = punti.tail(10)

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Media ultime 5", f"{ultime5.mean():.1f}")
                    c2.metric("Media ultime 10", f"{ultime10.mean():.1f}")
                    c3.metric("Massimo punti", f"{punti.max():.0f}")
                    c4.metric(
                        "Deviazione standard",
                        f"{punti.std():.1f}" if len(punti) > 1 else "N/D"
                    )

                    st.caption(
                        "Una deviazione standard più bassa indica "
                        "punti generalmente più costanti; non garantisce "
                        "che la prossima prestazione sarà simile."
                    )

            # PRODUZIONE PER 36 MINUTI
            if "MIN" in storico.columns:
                minuti = pd.to_numeric(
                    storico["MIN"], errors="coerce"
                )
                punti_num = pd.to_numeric(
                    storico["PTS"], errors="coerce"
                )

                minuti_medi = minuti.mean()
                minuti_totali = minuti.sum()

                st.subheader("Produzione per 36 minuti")

                if minuti_totali > 0:
                    punti_per36 = (
                        punti_num.sum() / minuti_totali * 36
                    )
                    st.metric(
                        "Punti per 36 minuti",
                        f"{punti_per36:.1f}"
                    )
                else:
                    st.info(
                        "Minuti non disponibili per calcolare "
                        "la produzione per 36 minuti."
                    )

                st.caption(
                    "La metrica normalizza i punti sul tempo giocato; "
                    "non rappresenta necessariamente il rendimento "
                    "che il giocatore avrebbe giocando 36 minuti."
                )

            # TURNOVER E RAPPORTO ASSIST/TURNOVER
            if "TOV" in storico.columns:
                turnover = pd.to_numeric(
                    storico["TOV"], errors="coerce"
                )

                st.subheader("Gestione della palla")
                col1, col2 = st.columns(2)
                col1.metric(
                    "Turnover medi",
                    f"{turnover.mean():.2f}"
                )

                if "AST" in storico.columns and turnover.sum() > 0:
                    assist = pd.to_numeric(
                        storico["AST"], errors="coerce"
                    )
                    rapporto = assist.sum() / turnover.sum()
                    col2.metric(
                        "Rapporto assist/turnover",
                        f"{rapporto:.2f}"
                    )
                else:
                    col2.metric("Rapporto assist/turnover", "N/D")

            st.subheader("Storico delle partite")
            st.dataframe(
                storico[colonne].sort_values(
                    "GAME_DATE", ascending=False
                ) if "GAME_DATE" in colonne
                else storico[colonne],
                use_container_width=True,
                hide_index=True,
            )

# ==================================================
# TAB 2 - SQUADRE
# ==================================================

with tab2:
    st.header("Analisi delle squadre")

    if "TEAM_NAME" not in squadre.columns:
        st.error("Manca la colonna TEAM_NAME nel CSV delle squadre.")
    else:
        nomi_squadre = sorted(
            squadre["TEAM_NAME"].dropna().unique().tolist()
        )

        squadra_scelta = st.selectbox(
            "Seleziona una squadra",
            nomi_squadre,
        )

        storico_squadra = squadre[
            squadre["TEAM_NAME"] == squadra_scelta
        ].copy()

        if "GAME_DATE" in storico_squadra.columns:
            storico_squadra["GAME_DATE"] = pd.to_datetime(
                storico_squadra["GAME_DATE"], errors="coerce"
            )
            storico_squadra = storico_squadra.sort_values("GAME_DATE")

        vittorie = (
            int(storico_squadra["WL"].eq("W").sum())
            if "WL" in storico_squadra.columns else 0
        )
        sconfitte = (
            int(storico_squadra["WL"].eq("L").sum())
            if "WL" in storico_squadra.columns else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Vittorie", vittorie)
        c2.metric("Sconfitte", sconfitte)
        c3.metric(
            "Punti medi",
            f"{storico_squadra['PTS'].mean():.1f}"
            if "PTS" in storico_squadra.columns else "N/D"
        )

        if (
            "GAME_DATE" in storico_squadra.columns
            and "PTS" in storico_squadra.columns
        ):
            st.subheader("Punti segnati nel tempo")
            st.line_chart(
                storico_squadra.dropna(
                    subset=["GAME_DATE", "PTS"]
                ).set_index("GAME_DATE")[["PTS"]]
            )

        st.subheader("Classifica per punti medi")

        if "PTS" in squadre.columns:
            classifica = (
                squadre.groupby("TEAM_NAME")
                .agg(
                    Punti_medi=("PTS", "mean"),
                    Partite=("PTS", "count"),
                )
                .round(1)
                .sort_values("Punti_medi", ascending=False)
            )

            st.dataframe(
                classifica,
                use_container_width=True,
            )

# ==================================================
# TAB 3 - PREVISIONI
# ==================================================

with tab3:
    st.header("Previsione sperimentale dei punti")
    st.write(
        "La stima usa le prestazioni recenti del giocatore. "
        "Non è una garanzia del risultato della prossima partita."
    )

    nomi_previsione = sorted(
        giocatori_filtrati["PLAYER_NAME"]
        .dropna().unique().tolist()
    ) if "PLAYER_NAME" in giocatori_filtrati.columns else []

    if nomi_previsione and "PTS" in giocatori_filtrati.columns:
        giocatore_pred = st.selectbox(
            "Giocatore da prevedere",
            nomi_previsione,
            key="giocatore_pred",
        )

        numero_partite = st.slider(
            "Partite recenti da analizzare",
            min_value=5,
            max_value=15,
            value=10,
        )

        storico_pred = giocatori_filtrati[
            giocatori_filtrati["PLAYER_NAME"] == giocatore_pred
        ].copy()

        if "GAME_DATE" in storico_pred.columns:
            storico_pred["GAME_DATE"] = pd.to_datetime(
                storico_pred["GAME_DATE"], errors="coerce"
            )
            storico_pred = storico_pred.sort_values("GAME_DATE")

        recenti = storico_pred.tail(numero_partite).copy()
        recenti["PTS"] = pd.to_numeric(
            recenti["PTS"], errors="coerce"
        )
        recenti = recenti.dropna(subset=["PTS"])

        if len(recenti) < 5:
            st.warning(
                "Servono almeno cinque partite valide per la stima."
            )
        else:
            media_recente = recenti["PTS"].mean()
            media_ultime_cinque = recenti.tail(5)["PTS"].mean()

            previsione = (
                0.7 * media_recente
                + 0.3 * media_ultime_cinque
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("Punti stimati", f"{previsione:.1f}")
            c2.metric("Media recente", f"{media_recente:.1f}")
            c3.metric(
                "Media ultime 5",
                f"{media_ultime_cinque:.1f}"
            )

            st.subheader("Prestazioni utilizzate")

            if "GAME_DATE" in recenti.columns:
                st.line_chart(
                    recenti.dropna(
                        subset=["GAME_DATE", "PTS"]
                    ).set_index("GAME_DATE")[["PTS"]]
                )
            else:
                st.line_chart(recenti[["PTS"]])

            st.info(
                "Modello iniziale basato sulle medie. "
                "Per migliorarlo aggiungeremo avversario, minuti, "
                "fattore campo e validazione sulle partite passate."
            )
    else:
        st.warning(
            "Non trovo le colonne necessarie per calcolare la stima."
        )

# ==================================================
# TAB 4 - CLASSIFICHE E DATI
# ==================================================

with tab4:
    st.header("Esplora i dati")

    scelta_dati = st.radio(
        "Tabella da visualizzare",
        ["Giocatori", "Squadre"],
        horizontal=True,
    )

    if scelta_dati == "Giocatori":
        st.write("Prime righe del dataset dei giocatori")
        st.dataframe(
            giocatori_filtrati.head(200),
            use_container_width=True,
        )
        st.download_button(
            "Scarica CSV giocatori filtrato",
            data=giocatori_filtrati.to_csv(index=False).encode("utf-8"),
            file_name="giocatori_filtrati.csv",
            mime="text/csv",
        )
    else:
        st.write("Prime righe del dataset delle squadre")
        st.dataframe(
            squadre.head(200),
            use_container_width=True,
        )
        st.download_button(
            "Scarica CSV squadre",
            data=squadre.to_csv(index=False).encode("utf-8"),
            file_name="squadre.csv",
            mime="text/csv",
        )

st.sidebar.markdown("---")
st.sidebar.caption("NBA Analytics Lab — prototipo in sviluppo")
