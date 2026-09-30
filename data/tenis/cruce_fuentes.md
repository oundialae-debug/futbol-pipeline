# Cruce tennis-data contra Sackmann y TennisMyLife

Generado por `modelos/tenis/scripts/cruce_fuentes.py`. Cada fila de tennis-data
(2020-2026) se busca en la otra fuente. "ganador distinto" = mismo partido con
ganador y perdedor al revés. Marcador comparado solo en partidos completos
(`Comment == Completed`), por juegos de cada set.

| circuito | fuente | partidos td (en su rango) | emparejados | ganador distinto | sin encontrar | marcador distinto | superficie distinta |
|---|---|---|---|---|---|---|---|
| ATP | Sackmann | 15741 | 15176 (96.4%) | 4 | 561 (3.6%) | 46 de 14647 (0.31%) | 51 |
| ATP | TennisMyLife | 16642 | 16243 (97.6%) | 5 | 394 (2.4%) | 48 de 15694 (0.31%) | 81 |
| WTA | Sackmann | 14614 | 14158 (96.9%) | 8 | 448 (3.1%) | 37 de 13605 (0.27%) | 114 |
| WTA | TennisMyLife | 15548 | 15057 (96.8%) | 24 | 467 (3.0%) | 141 de 14470 (0.97%) | 114 |

## ATP Sackmann

Sin encontrar, por año: 2020: 28, 2021: 69, 2022: 81, 2023: 104, 2024: 103, 2025: 126, 2026: 50
Sin encontrar, por tipo de torneo: ATP250: 285, Masters 1000: 105, ATP500: 90, Grand Slam: 81
- ganador distinto: 2021-11-14 Masters Cup: td Berrettini M. gana a Zverev A. (6-7 0-1); Sackmann: Alexander Zverev gana a Matteo Berrettini (7-6(7) 1-0 RET)
- ganador distinto: 2026-02-10 ABN AMRO World Tennis Tournament: td Bergs Z. gana a Medjedovic H. (6-7 6-7); Sackmann: Hamad Medjedovic gana a Zizou Bergs (7-6(5) 7-6(5))
- ganador distinto: 2023-04-06 Grand Prix Hassan II: td Kuzmanov D. gana a Carballes Baena R. (0-2); Sackmann: Roberto Carballes Baena gana a Dimitar Kuzmanov (2-0 RET)
- ganador distinto: 2024-11-14 Masters Cup: td De Minaur A. gana a Fritz T. (5-7 6-4 6-3); Sackmann: Taylor Fritz gana a Alex De Minaur (5-7 6-4 6-3)
- marcador: 2025-08-25 US Open Bellucci M. - Shang J.: td '7-6 1-6 6-3' / Sackmann '7-6(0) 1-6 6-3 3-0 RET'
- marcador: 2023-08-01 Generali Open Rinderknech A. - Cerundolo J.M.: td '6-7 6-4 6-3' / Sackmann '6-7(3) 6-4 6-2'
- marcador: 2025-10-26 Vienna Open Sinner J. - Zverev A.: td '3-6 6-3 7-5' / Sackmann '6-0 6-1'
- marcador: 2021-03-07 ABN AMRO World Tennis Tournament Rublev A. - Fucsovics M.: td '7-6 6-4' / Sackmann 'W/O'
- marcador: 2025-04-01 Tiriac Open Diallo G. - Tseng C.H.: td '7-6' / Sackmann '7-6(5) 7-6(2)'
- superficie: 2021-04-05 Sardegna Open: td Hard / Sackmann Clay
- superficie: 2021-04-05 Sardegna Open: td Hard / Sackmann Clay
- superficie: 2021-04-05 Sardegna Open: td Hard / Sackmann Clay
- sin encontrar: 2021-03-11 Chile Open Varillas J. P. - Coria F. (2nd Round)
- sin encontrar: 2025-05-21 Hamburg Open Auger-Aliassime F. - Mpetshi G. (2nd Round)
- sin encontrar: 2023-04-26 Mutua Madrid Open Ramos-Vinolas A. - Ivashka I. (1st Round)
- sin encontrar: 2026-02-09 ABN AMRO World Tennis Tournament O Connell C. - Royer V. (1st Round)
- sin encontrar: 2025-04-15 BMW Open Darderi L. - O Connell C. (1st Round)

## ATP TennisMyLife

Sin encontrar, por año: 2020: 6, 2021: 20, 2022: 29, 2023: 70, 2024: 77, 2025: 88, 2026: 104
Sin encontrar, por tipo de torneo: ATP250: 189, Masters 1000: 83, Grand Slam: 66, ATP500: 56
- ganador distinto: 2021-11-14 Masters Cup: td Berrettini M. gana a Zverev A. (6-7 0-1); TennisMyLife: Alexander Zverev gana a Matteo Berrettini (7-6(7) 1-0 RET)
- ganador distinto: 2026-02-10 ABN AMRO World Tennis Tournament: td Bergs Z. gana a Medjedovic H. (6-7 6-7); TennisMyLife: Hamad Medjedovic gana a Zizou Bergs (7-6(5) 7-6(5))
- ganador distinto: 2023-10-04 Shanghai Masters: td Kecmanovic M. gana a Bu Y. (7-6 2-6 1-2); TennisMyLife: Yunchaokete Bu gana a Miomir Kecmanovic (6-7(6) 6-2 2-1 RET)
- ganador distinto: 2023-04-06 Grand Prix Hassan II: td Kuzmanov D. gana a Carballes Baena R. (0-2); TennisMyLife: Roberto Carballes Baena gana a Dimitar Kuzmanov (2-0 RET)
- ganador distinto: 2024-11-14 Masters Cup: td De Minaur A. gana a Fritz T. (5-7 6-4 6-3); TennisMyLife: Taylor Fritz gana a Alex de Minaur (5-7 6-4 6-3)
- marcador: 2026-07-05 Wimbledon Djokovic N. - Safiullin R.: td '7-6 6-3 3-6 6-3' / TennisMyLife '7-6(6) 6-3 3-6 6-2'
- marcador: 2026-07-07 Wimbledon Zverev A. - Lehecka J.: td '6-4 7-5 3-6 7-6' / TennisMyLife '6-4 7-5 3-6 6-3'
- marcador: 2026-01-21 Australian Open Alcaraz C. - Hanfmann Y.: td '7-6 6-3 6-2' / TennisMyLife '7-6(4) 6-4 6-3'
- marcador: 2025-04-01 Tiriac Open Diallo G. - Tseng C.H.: td '7-6' / TennisMyLife '7-6(5) 7-6(2)'
- marcador: 2022-10-25 Vienna Open Dimitrov G. - Monteiro T.: td '6-3 6-3' / TennisMyLife '6-3 6-4'
- superficie: 2021-04-05 Sardegna Open: td Hard / TennisMyLife Clay
- superficie: 2021-04-05 AnyTech365 Andalucia Open: td Hard / TennisMyLife Clay
- superficie: 2021-04-05 AnyTech365 Andalucia Open: td Hard / TennisMyLife Clay
- sin encontrar: 2023-04-20 Srpska Open Rublev A. - Varillas J. P. (2nd Round)
- sin encontrar: 2025-04-04 Tiriac Open Fucsovics M. - O Connell C. (Quarterfinals)
- sin encontrar: 2026-07-01 Wimbledon Medvedev D. - Merida Aguilar D. (2nd Round)
- sin encontrar: 2023-10-20 European Open Bublik A. - Mpetshi G. (Quarterfinals)
- sin encontrar: 2025-01-14 Australian Open Monfils G. - Mpetshi G. (1st Round)

## WTA Sackmann

Sin encontrar, por año: 2020: 40, 2021: 115, 2022: 99, 2023: 59, 2024: 47, 2025: 50, 2026: 38
Sin encontrar, por tipo de torneo: WTA250: 212, Grand Slam: 81, WTA1000: 78, WTA500: 53, International: 17, Premier: 7
- ganador distinto: 2020-01-13 Hobart International: td Peterson R. gana a Ferro F. (4-4); Sackmann: Fiona Ferro gana a Rebecca Peterson (4-4 RET)
- ganador distinto: 2022-02-15 Dubai Duty Free Tennis Championships: td Collins D. gana a Vondrousova M. (6-2 0-3); Sackmann: Marketa Vondrousova gana a Danielle Collins (2-6 3-0)
- ganador distinto: 2023-04-04 Copa Colsanitas: td Tan H. gana a Arango E. (5-7 1-3); Sackmann: Emiliana Arango gana a Harmony Tan (7-5 3-1 RET)
- ganador distinto: 2020-01-15 Adelaide International: td Kerber A. gana a Yastremska D. (3-6 0-2); Sackmann: Dayana Yastremska gana a Angelique Kerber (6-3 2-0 RET)
- ganador distinto: 2024-09-11 Guadalajara Open: td Azarenka V. gana a Rakhimova K. (2-6 0-3); Sackmann: Kamilla Rakhimova gana a Victoria Azarenka (6-2 3-0 RET)
- marcador: 2024-01-08 Adelaide International Bogdan A. - Boulter K.: td '6-4' / Sackmann '6-3 6-4'
- marcador: 2023-10-16 Jiangxi Tennis Open Anshba A. - Avanesyan E.: td '7-6 6-4' / Sackmann '2-6 7-6(4) 6-4'
- marcador: 2023-01-30 Thailand Open Zhu L. - Wang Xiy.: td '4-6 6-3 6-0' / Sackmann '6-2 6-4'
- marcador: 2024-10-14 Japan Open Lamens S. - Tomova V.: td '6-0 6-2' / Sackmann '6-1 6-2'
- marcador: 2026-03-04 BNP Paribas Open Putintseva Y. - Badosa P.: td '6-4 6-2 0-0' / Sackmann '6-4 6-2'
- superficie: 2020-02-24 Abierto Mexicano: td Clay / Sackmann Hard
- superficie: 2020-02-24 Abierto Mexicano: td Clay / Sackmann Hard
- superficie: 2020-02-24 Abierto Mexicano: td Clay / Sackmann Hard
- sin encontrar: 2022-04-04 Copa Colsanitas Peterson R. - Herazo M. (1st Round)
- sin encontrar: 2023-07-05 Wimbledon Juvan K. - Betova M. (1st Round)
- sin encontrar: 2022-03-24 Miami Open Riske A. - Cornet A. (2nd Round)
- sin encontrar: 2020-09-02 US Open Kvitova P. - Kozlova K. (2nd Round)
- sin encontrar: 2023-01-16 Australian Open Wang Xin. - Sanders S. (1st Round)

## WTA TennisMyLife

Sin encontrar, por año: 2020: 40, 2021: 115, 2022: 99, 2023: 59, 2024: 52, 2025: 55, 2026: 47
Sin encontrar, por tipo de torneo: WTA250: 213, Grand Slam: 89, WTA1000: 82, WTA500: 54, International: 17, Premier: 7, Tour Championships: 5
- ganador distinto: 2020-01-13 Hobart International: td Peterson R. gana a Ferro F. (4-4); TennisMyLife: Fiona Ferro gana a Rebecca Peterson (4-4 RET)
- ganador distinto: 2026-04-13 Open de Rouen: td Boulter K. gana a Timofeeva M. (6-2 6-2); TennisMyLife: Maria Timofeeva gana a Katie Boulter (6-2 6-2)
- ganador distinto: 2026-04-13 Open de Rouen: td Li A. gana a Kasatkina D. (6-7 6-2 6-4); TennisMyLife: Daria Kasatkina gana a Ann Li (6-7(6),6-2 6-4)
- ganador distinto: 2026-04-13 Open de Rouen: td Podrez V. gana a Stephens S. (6-2 6-1); TennisMyLife: Sloane Stephens gana a Veronika Podrez ( 6-2 6-1)
- ganador distinto: 2026-04-14 Open de Rouen: td Salkova D. gana a Blinkova A. (7-5 6-1); TennisMyLife: Anna Blinkova gana a Dominika Salkova (7-5 6-1)
- marcador: 2024-01-08 Adelaide International Bogdan A. - Boulter K.: td '6-4' / TennisMyLife '6-3 6-4'
- marcador: 2023-10-16 Jiangxi Tennis Open Anshba A. - Avanesyan E.: td '7-6 6-4' / TennisMyLife '2-6 7-6(4) 6-4'
- marcador: 2026-08-13 Canadian Open Swiatek I. - Rybakina E.: td '6-2 6-3' / TennisMyLife '4-1 RET'
- marcador: 2024-10-14 Japan Open Lamens S. - Tomova V.: td '6-0 6-2' / TennisMyLife '6-1 6-2'
- marcador: 2026-06-15 Nottingham Open Starodubtseva Y. - Joint M.: td '6-7 7-5 6-4' / TennisMyLife '7-6(8) 5-7 4-6'
- superficie: 2020-02-24 Abierto Mexicano: td Clay / TennisMyLife Hard
- superficie: 2020-02-24 Abierto Mexicano: td Clay / TennisMyLife Hard
- superficie: 2020-02-24 Abierto Mexicano: td Clay / TennisMyLife Hard
- sin encontrar: 2023-06-26 Eastbourne International Osorio M. - Rogers S. (1st Round)
- sin encontrar: 2026-03-31 Copa Colsanitas Osorio M. - Dolehide C. (1st Round)
- sin encontrar: 2023-05-31 French Open Mertens E. - Osorio M. (2nd Round)
- sin encontrar: 2022-08-11 Canadian Open Putintseva Y. - Riske A. (3rd Round)
- sin encontrar: 2021-04-06 Volvo Car Open Kvitova P. - Sanders S. (2nd Round)
