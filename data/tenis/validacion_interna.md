# Validación interna de partidos (desde 2000)

Generado por `modelos/tenis/scripts/validar_interno.py`.

| fuente | partidos | con stats | stats imposibles | texto en numéricas | duplicados | ganador=perdedor | retirada/WO | sin marcador |
|---|---|---|---|---|---|---|---|---|
| Sackmann ATP | 79299 | 72262 (91%) | 0 | 0 | 2 | 0 | 2807 (3.5%) | 0 |
| Sackmann Challenger+previas ATP | 137088 | 133458 (97%) | 0 | 0 | 4 | 3 | 5359 (3.9%) | 30 |
| Sackmann WTA | 72714 | 47827 (66%) | 1 | 0 | 0 | 0 | 2385 (3.3%) | 0 |
| Sackmann previas+ITF WTA | 363168 | 54171 (15%) | 1 | 0 | 1354 | 4 | 12736 (3.5%) | 182 |
| TennisMyLife ATP | 80373 | 73648 (92%) | 8 | 0 | 10 | 0 | 2853 (3.5%) | 2 |
| TennisMyLife Challenger | 79481 | 77997 (98%) | 0 | 1 | 36 | 0 | 3220 (4.1%) | 0 |
| TennisMyLife previas ATP | 24612 | 23828 (97%) | 12 | 0 | 1 | 0 | 720 (2.9%) | 0 |
| TennisMyLife WTA | 72224 | 48562 (67%) | 3 | 1 | 0 | 0 | 2397 (3.3%) | 1 |

## Sackmann WTA

- regla w_1stWon>w_1stIn: 1
- regla w_1stWon+w_2ndWon>w_svpt: 1
- regla l_1stWon>l_1stIn: 1
- regla l_1stWon+l_2ndWon>l_svpt: 1
- imposible: wta_matches_2023.csv 20231107 Marie Bouzkova - Viktorija Golubic

## Sackmann previas+ITF WTA

- regla l negativo: 1
- imposible: wta_matches_qual_itf_2025.csv 20251027 Benedetta Ortenzi - Valentina Abril Bruno

## TennisMyLife ATP

- regla w_ace+w_df>w_svpt: 1
- regla w_1stIn>w_svpt: 4
- regla w_1stWon+w_2ndWon>w_svpt: 1
- regla w_bpSaved>w_bpFaced: 4
- regla l_ace+l_df>l_svpt: 1
- regla l_1stWon>l_1stIn: 1
- regla l_bpSaved>l_bpFaced: 3
- imposible: 2016.csv 20160808 Kei Nishikori - Rafael Nadal
- imposible: 2019.csv 20190520 Benoit Paire - Felix Auger-Aliassime
- imposible: 2023.csv 20230410 Andrey Rublev - Holger Rune
- imposible: 2025.csv 20250912 Soonwoo Kwon - Alexander Bublik
- imposible: 2025.csv 20250912 Cameron Norrie - Olaf Pieczkowski
- imposible: 2025.csv 20250912 Sumit Nagal - Henry Bernet
- imposible: 2025.csv 20250912 Tomas Barrios Vera - Alex Knaff
- imposible: 2026.csv 20260206 Thiago Agustin Tirante - Hyeon Chung

## TennisMyLife Challenger

- texto: 2026_challenger.csv: l_bpFaced='4y' (Javier Barranco Cosano - Martin Krumich)

## TennisMyLife previas ATP

- regla w_bpSaved>w_bpFaced: 9
- regla l_bpSaved>l_bpFaced: 5
- imposible: 2026_atp_quali.csv 20260524 Jesper de Jong - Fajing Sun
- imposible: 2026_atp_quali.csv 20260524 Toby Samuel - Martin Damm
- imposible: 2026_atp_quali.csv 20260524 Vilius Gaubas - Federico Coria
- imposible: 2026_atp_quali.csv 20260524 August Holmgren - Otto Virtanen
- imposible: 2026_atp_quali.csv 20260524 Jay Clarke - Dane Sweeny
- imposible: 2026_atp_quali.csv 20260524 Lukas Neumayer - Alex Bolt
- imposible: 2026_atp_quali.csv 20260524 Ugo Blanchet - Charles Broom
- imposible: 2026_atp_quali.csv 20260524 Gonzalo Bueno - Florent Bax
- imposible: 2026_atp_quali.csv 20260524 Facundo Diaz Acosta - Christopher O'Connell
- imposible: 2026_atp_quali.csv 20260524 Liam Draxl - Ilia Simakin

## TennisMyLife WTA

- regla w_ace+w_df>w_svpt: 1
- regla w_1stIn>w_svpt: 1
- regla w_1stWon>w_1stIn: 1
- regla w_1stWon+w_2ndWon>w_svpt: 2
- regla w_bpSaved>w_bpFaced: 1
- regla l_ace+l_df>l_svpt: 1
- regla l_1stIn>l_svpt: 1
- regla l_1stWon>l_1stIn: 2
- regla l_1stWon+l_2ndWon>l_svpt: 2
- regla l_bpSaved>l_bpFaced: 1
- texto: 2026_wta.csv: l_2ndWon='-35.9%' (Xiyu Wang - Yuliia Starodubtseva)
- imposible: 2023_wta.csv 20231107 Marie Bouzkova - Viktorija Golubic
- imposible: 2025_wta.csv 20250106 Elise Mertens - Nuria Parrizas Diaz
- imposible: 2026_wta.csv 20260524 Xiyu Wang - Yuliia Starodubtseva
