# Prueba de API-Tennis

get_livescore: 61 partidos en juego.
Campos: event_date, event_final_result, event_first_player, event_first_player_logo, event_game_result, event_key, event_live, event_qualification, event_second_player, event_second_player_logo, event_serve, event_status, event_time, event_type_type, event_winner, first_player_dp1_key, first_player_dp2_key, first_player_key, pointbypoint, scores, second_player_dp1_key, second_player_dp2_key, second_player_key, statistics, tournament_key, tournament_name, tournament_round, tournament_season

Tipos: {'Itf Women Singles': 18, 'Itf Men Singles': 23, 'Challenger Women Singles': 4, 'Itf Men Doubles': 4, 'Challenger Men Singles': 4, 'Atp Singles': 2, 'Challenger Men Doubles': 4, 'Wta Singles': 2}

Ejemplo (sin punto a punto ni estadísticas):
```
{
 "event_key": 12167104,
 "event_date": "2026-09-30",
 "event_time": "10:30",
 "event_first_player": "P. Berezina",
 "first_player_key": 75362,
 "first_player_dp1_key": null,
 "first_player_dp2_key": null,
 "event_second_player": "A. Kumru",
 "second_player_key": 38327,
 "second_player_dp1_key": null,
 "second_player_dp2_key": null,
 "event_final_result": "0 - 1",
 "event_game_result": "0 - 0",
 "event_serve": "Second Player",
 "event_winner": null,
 "event_status": "Set 2",
 "event_type_type": "Itf Women Singles",
 "tournament_name": "W15 Monastir 28",
 "tournament_key": 4325,
 "tournament_round": "W15 Monastir 28 - 1/16-finals",
 "tournament_season": "2026",
 "event_live": "1",
 "event_first_player_logo": null,
 "event_second_player_logo": "https://api.api-tennis.com/logo-tennis/38327_a-kumru.jpg",
 "event_qualification": "False",
 "scores": [
  {
   "score_first": "2",
   "score_second": "6",
   "score_set": "1"
  },
  {
   "score_first": "5",
   "score_second": "4",
   "score_set": "2"
  }
 ]
}
```
Punto a punto, primeros elementos:
```
[{"set_number": "Set 1", "number_game": "1", "player_served": "First Player", "serve_winner": "Second Player", "serve_lost": "First Player", "score": "0 - 1", "points": [{"number_point": "1", "score": "0 - 15", "break_point": null, "set_point": null, "match_point": null}, {"number_point": "2", "score": "0 - 30", "break_point": null, "set_point": null, "match_point": null}, {"number_point": "3", "score": "0 - 40", "break_point": null, "set_point": null, "match_point": null}]}, {"set_number": "Set 1", "number_game": "2", "player_served": "Second Player", "serve_winner": "First Player", "serve_lost": "Second Player", "score": "1 - 1", "points": [{"number_point": "1", "score": "15 - 0", "break_point": null, "set_point": null, "match_point": null}, {"number_point": "2", "score": "15 - 15", "break_point": null, "set_point": null, "match_point": null}, {"number_point": "3", "score": "30 - 15", "break_point": null, "set_point": null, "match_point": null}, {"number_point": "4", "score": "40 - 15", "break_point": null, "set_point": null, "match_point": null}]}]
```

| partido | tipo | estado bruto | marcador traducido |
|---|---|---|---|
| P. Berezina vs A. Kumru | Itf Women Singles | Set 2 / 0 - 0 / saca Second Player / [('1', '2', '6'), ('2', '5', '4')] | {'sa': 0, 'sb': 1, 'ga': 5, 'gb': 4, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (2, 6), 'mejor_de': 3} |
| S. Paardekooper vs G. Misasi | Itf Men Singles | Set 3 / 4 - 5 / saca First Player / [('1', '0', '6'), ('2', '6', '3'), ('3', '6', '6')] | {'sa': 1, 'sb': 1, 'ga': 6, 'gb': 6, 'xa': 4, 'xb': 3, 'a_saca': True, 'previos': (6, 9), 'mejor_de': 3} |
| G. Bosio vs K. Malirz | Itf Men Singles | Set 1 / 0 - 0 / saca Second Player / [('1', '5', '3')] | {'sa': 0, 'sb': 0, 'ga': 5, 'gb': 3, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| T. Sach vs J. Beale | Itf Men Singles | Set 3 / 30 - 0 / saca First Player / [('1', '6', '4'), ('2', '3', '6'), ('3', '2', '4')] | {'sa': 1, 'sb': 1, 'ga': 2, 'gb': 4, 'xa': 2, 'xb': 0, 'a_saca': True, 'previos': (9, 10), 'mejor_de': 3} |
| L. Boisson vs M. Kubka | Challenger Women Singles | Set 2 / 0 - 0 / saca First Player / [('1', '6', '3'), ('2', '2', '1')] | {'sa': 1, 'sb': 0, 'ga': 2, 'gb': 1, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (6, 3), 'mejor_de': 3} |
| M. Krivoshchekov vs M. Elesin | Itf Men Singles | Set 3 / 30 - 0 / saca First Player / [('1', '6', '3'), ('2', '1', '6'), ('3', '4', '4')] | {'sa': 1, 'sb': 1, 'ga': 4, 'gb': 4, 'xa': 2, 'xb': 0, 'a_saca': True, 'previos': (7, 9), 'mejor_de': 3} |
| M. Walters vs E. Kypriotis | Itf Men Singles | Set 3 / 15 - 15 / saca Second Player / [('1', '6', '3'), ('2', '1', '6'), ('3', '1', '0')] | {'sa': 1, 'sb': 1, 'ga': 1, 'gb': 0, 'xa': 1, 'xb': 1, 'a_saca': False, 'previos': (7, 9), 'mejor_de': 3} |
| A. Colombo vs E. Lumsden | Itf Men Singles | Set 2 / 15 - 15 / saca First Player / [('1', '6', '4'), ('2', '0', '3')] | {'sa': 1, 'sb': 0, 'ga': 0, 'gb': 3, 'xa': 1, 'xb': 1, 'a_saca': True, 'previos': (6, 4), 'mejor_de': 3} |
| J. Echeverria vs L. G. Verwerft | Itf Men Singles | Set 1 / 0 - 0 / saca First Player / [('1', '5', '6')] | {'sa': 0, 'sb': 0, 'ga': 5, 'gb': 6, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| R. Lefevre vs J. Loge | Itf Men Singles | Set 3 / 0 - 0 / saca First Player / [('1', '3', '6'), ('2', '6', '3')] | {'sa': 1, 'sb': 1, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (9, 9), 'mejor_de': 3} |
| V. Ryden vs A. Ouakaa | Itf Men Singles | Set 2 / 30 - 15 / saca Second Player / [('1', '3', '6'), ('2', '1', '2')] | {'sa': 0, 'sb': 1, 'ga': 1, 'gb': 2, 'xa': 2, 'xb': 1, 'a_saca': False, 'previos': (3, 6), 'mejor_de': 3} |
| M. Krajci vs P. O. Fellin | Itf Men Singles | Set 1 / A - 40 / saca Second Player / [('1', '5', '4')] | {'sa': 0, 'sb': 0, 'ga': 5, 'gb': 4, 'xa': 4, 'xb': 3, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| F. Livet Novkirichka vs G. El Feky | Itf Men Singles | Set 1 / 0 - 0 / saca Second Player / [('1', '0', '2')] | {'sa': 0, 'sb': 0, 'ga': 0, 'gb': 2, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| F. Zakaria vs K. Ibrahim | Itf Men Singles | Set 1 / 30 - 40 / saca Second Player / [('1', '3', '3')] | {'sa': 0, 'sb': 0, 'ga': 3, 'gb': 3, 'xa': 2, 'xb': 3, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| K. Kajin vs S. Seghetti | Itf Men Singles | Finished / - / saca None / [('1', '4', '6'), ('2', '2', '6')] | None |
| R. Zuberbuehler vs A. Battiston | Itf Men Singles | Set 3 / 0 - 0 / saca First Player / [('1', '3', '6'), ('2', '7', '6')] | {'sa': 1, 'sb': 1, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (10, 12), 'mejor_de': 3} |
| E. Andreeva vs S. Waltert | Challenger Women Singles | Set 2 / 0 - 0 / saca First Player / [('1', '6', '3')] | {'sa': 1, 'sb': 0, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (6, 3), 'mejor_de': 3} |
| S. Biolay vs K. Kroitor | Itf Women Singles | Set 2 / 0 - 0 / saca First Player / [('1', '6', '2'), ('2', '4', '1')] | {'sa': 1, 'sb': 0, 'ga': 4, 'gb': 1, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (6, 2), 'mejor_de': 3} |
| M. Lazarenko vs Mat. Mariani | Itf Women Singles | Set 2 / 40 - 40 / saca First Player / [('1', '2', '6'), ('2', '2', '4')] | {'sa': 0, 'sb': 1, 'ga': 2, 'gb': 4, 'xa': 3, 'xb': 3, 'a_saca': True, 'previos': (2, 6), 'mejor_de': 3} |
| K. Ruchkina vs K. Blazkova | Itf Women Singles | Set 2 / 40 - A / saca Second Player / [('1', '6', '3'), ('2', '2', '0')] | {'sa': 1, 'sb': 0, 'ga': 2, 'gb': 0, 'xa': 3, 'xb': 4, 'a_saca': False, 'previos': (6, 3), 'mejor_de': 3} |
| C. Brace vs E. Tomase | Itf Women Singles | Set 1 / 0 - 0 / saca First Player / [('1', '4', '1')] | {'sa': 0, 'sb': 0, 'ga': 4, 'gb': 1, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| M. Ngounoue vs A. M. Coromina Boluda | Itf Women Singles | Set 1 / 40 - 40 / saca First Player / [('1', '2', '3')] | {'sa': 0, 'sb': 0, 'ga': 2, 'gb': 3, 'xa': 3, 'xb': 3, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| K. Novak vs M. Teixido Garcia | Itf Women Singles | Set 1 / 40 - 30 / saca First Player / [('1', '1', '3')] | {'sa': 0, 'sb': 0, 'ga': 1, 'gb': 3, 'xa': 3, 'xb': 2, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| S. Baslilar vs H. Im | Itf Women Singles | Finished / - / saca None / [('1', '3', '6'), ('2', '3', '6')] | None |
| M. Ciocan vs M. Szostak | Itf Women Singles | Set 1 / 0 - 0 / saca First Player / [('1', '3', '3')] | {'sa': 0, 'sb': 0, 'ga': 3, 'gb': 3, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| S. Avataneo vs V. Salaiova | Itf Women Singles | Set 2 / 0 - 0 / saca Second Player / [('1', '6', '3'), ('2', '3', '1')] | {'sa': 1, 'sb': 0, 'ga': 3, 'gb': 1, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (6, 3), 'mejor_de': 3} |
| S. Samir vs L. Rothensteiner | Itf Women Singles | Set 2 / 40 - 40 / saca Second Player / [('1', '6', '2'), ('2', '5', '5')] | {'sa': 1, 'sb': 0, 'ga': 5, 'gb': 5, 'xa': 3, 'xb': 3, 'a_saca': False, 'previos': (6, 2), 'mejor_de': 3} |
| A. Vasileva vs A. Sushkova | Itf Women Singles | Set 2 / 30 - 40 / saca Second Player / [('1', '1', '6'), ('2', '0', '2')] | {'sa': 0, 'sb': 1, 'ga': 0, 'gb': 2, 'xa': 2, 'xb': 3, 'a_saca': False, 'previos': (1, 6), 'mejor_de': 3} |
| J. Stamatova vs O. Simion | Itf Women Singles | Set 2 / 0 - 0 / saca First Player / [('1', '7', '6'), ('2', '2', '5')] | {'sa': 1, 'sb': 0, 'ga': 2, 'gb': 5, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (7, 6), 'mejor_de': 3} |
| S. Zhenikhova vs K. Supova | Itf Women Singles | Set 2 / 40 - 15 / saca First Player / [('1', '6', '4'), ('2', '4', '3')] | {'sa': 1, 'sb': 0, 'ga': 4, 'gb': 3, 'xa': 3, 'xb': 1, 'a_saca': True, 'previos': (6, 4), 'mejor_de': 3} |
| A. Nefve vs A. Beckley | Itf Men Singles | Set 1 / 0 - 15 / saca Second Player / [('1', '5', '4')] | {'sa': 0, 'sb': 0, 'ga': 5, 'gb': 4, 'xa': 0, 'xb': 1, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| P. Henning vs T. Schoolkate | Challenger Men Singles | Set 2 / 0 - 0 / saca Second Player / [('1', '3', '6'), ('2', '1', '2')] | {'sa': 0, 'sb': 1, 'ga': 1, 'gb': 2, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (3, 6), 'mejor_de': 3} |
| M. Arnaldi vs R. Sakamoto | Atp Singles | Set 2 / 40 - 30 / saca First Player / [('1', '2', '6'), ('2', '3', '3')] | {'sa': 0, 'sb': 1, 'ga': 3, 'gb': 3, 'xa': 3, 'xb': 2, 'a_saca': True, 'previos': (2, 6), 'mejor_de': 3} |
| T. Preston vs T. Korpatsch | Wta Singles | Set 2 / 30 - 30 / saca Second Player / [('1', '6', '2'), ('2', '3', '3')] | {'sa': 1, 'sb': 0, 'ga': 3, 'gb': 3, 'xa': 2, 'xb': 2, 'a_saca': False, 'previos': (6, 2), 'mejor_de': 3} |
| S. Ryan Ziegann vs Ja. Delaney | Itf Men Singles | Set 1 / 15 - 15 / saca First Player / [('1', '3', '5')] | {'sa': 0, 'sb': 0, 'ga': 3, 'gb': 5, 'xa': 1, 'xb': 1, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| S. Vujic vs C. Sinclair | Itf Men Singles | Set 1 / 0 - 0 / saca First Player / [('1', '0', '0')] | {'sa': 0, 'sb': 0, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| A. Ruzic vs J. Riera | Challenger Women Singles | Set 2 / 30 - 0 / saca Second Player / [('1', '6', '3'), ('2', '1', '1')] | {'sa': 1, 'sb': 0, 'ga': 1, 'gb': 1, 'xa': 2, 'xb': 0, 'a_saca': False, 'previos': (6, 3), 'mejor_de': 3} |
| S. A. Andreescu vs R. M. Papoe | Itf Men Singles | Set 1 / 40 - 40 / saca Second Player / [('1', '3', '2')] | {'sa': 0, 'sb': 0, 'ga': 3, 'gb': 2, 'xa': 3, 'xb': 3, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| R. Guna vs F. Broska | Itf Men Singles | Set 2 / 0 - 0 / saca Second Player / [('1', '2', '6'), ('2', '2', '2')] | {'sa': 0, 'sb': 1, 'ga': 2, 'gb': 2, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (2, 6), 'mejor_de': 3} |
| F. J. Planinsek vs A. Berge Nourescu | Itf Men Singles | Set 2 / 40 - 30 / saca First Player / [('1', '6', '1'), ('2', '2', '1')] | {'sa': 1, 'sb': 0, 'ga': 2, 'gb': 1, 'xa': 3, 'xb': 2, 'a_saca': True, 'previos': (6, 1), 'mejor_de': 3} |
| V. Vanta vs L. Pokorny | Itf Men Singles | Set 1 / 40 - 30 / saca First Player / [('1', '0', '0')] | {'sa': 0, 'sb': 0, 'ga': 0, 'gb': 0, 'xa': 3, 'xb': 2, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| L. Broady vs D. Stricker | Challenger Men Singles | Set 2 / 0 - 0 / saca Second Player / [('1', '4', '6'), ('2', '2', '1')] | {'sa': 0, 'sb': 1, 'ga': 2, 'gb': 1, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (4, 6), 'mejor_de': 3} |
| M. Vankan vs C. Amadike | Itf Men Singles | Set 2 / 15 - 0 / saca Second Player / [('1', '6', '0'), ('2', '2', '2')] | {'sa': 1, 'sb': 0, 'ga': 2, 'gb': 2, 'xa': 1, 'xb': 0, 'a_saca': False, 'previos': (6, 0), 'mejor_de': 3} |
| A. Venkataraman vs N. Grunewald | Itf Men Singles | Set 2 / 0 - 15 / saca Second Player / [('1', '2', '6'), ('2', '1', '2')] | {'sa': 0, 'sb': 1, 'ga': 1, 'gb': 2, 'xa': 0, 'xb': 1, 'a_saca': False, 'previos': (2, 6), 'mejor_de': 3} |
| N. Bains vs M. Martinez Vaquero | Itf Women Singles | Set 2 / 30 - 15 / saca Second Player / [('1', '2', '6'), ('2', '3', '1')] | {'sa': 0, 'sb': 1, 'ga': 3, 'gb': 1, 'xa': 2, 'xb': 1, 'a_saca': False, 'previos': (2, 6), 'mejor_de': 3} |
| R. Brantmeier vs K. Swan | Itf Women Singles | Set 1 / 15 - 0 / saca First Player / [('1', '4', '5')] | {'sa': 0, 'sb': 0, 'ga': 4, 'gb': 5, 'xa': 1, 'xb': 0, 'a_saca': True, 'previos': (0, 0), 'mejor_de': 3} |
| A. Nagy vs A. Voloshchuk | Itf Women Singles | Set 2 / 0 - 0 / saca First Player / [('1', '6', '4'), ('2', '5', '0')] | {'sa': 1, 'sb': 0, 'ga': 5, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': True, 'previos': (6, 4), 'mejor_de': 3} |
| T. J. Brockmann vs D. Tran | Itf Women Singles | Set 1 / 0 - 0 / saca Second Player / [('1', '0', '0')] | {'sa': 0, 'sb': 0, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| W. Zheng vs S. Sorribes Tormo | Challenger Women Singles | Set 3 / 15 - 0 / saca First Player / [('1', '6', '4'), ('2', '2', '6'), ('3', '3', '4')] | {'sa': 1, 'sb': 1, 'ga': 3, 'gb': 4, 'xa': 1, 'xb': 0, 'a_saca': True, 'previos': (8, 10), 'mejor_de': 3} |
| Z. Zhang vs A. Gea | Atp Singles | Set 1 / 0 - 0 / saca None / [('1', '0', '0')] | {'sa': 0, 'sb': 0, 'ga': 0, 'gb': 0, 'xa': 0, 'xb': 0, 'a_saca': None, 'previos': (0, 0), 'mejor_de': 3} |
| M. Hontama vs K. Boulter | Wta Singles | Set 1 / 0 - 0 / saca Second Player / [('1', '2', '3')] | {'sa': 0, 'sb': 0, 'ga': 2, 'gb': 3, 'xa': 0, 'xb': 0, 'a_saca': False, 'previos': (0, 0), 'mejor_de': 3} |
| G. Cadenasso vs L. Angelini | Challenger Men Singles | Set 2 / 30 - 0 / saca First Player / [('1', '5', '7'), ('2', '1', '3')] | {'sa': 0, 'sb': 1, 'ga': 1, 'gb': 3, 'xa': 2, 'xb': 0, 'a_saca': True, 'previos': (5, 7), 'mejor_de': 3} |
| J. C. Martin Manzano vs J. Clarke | Challenger Men Singles | Set 2 / 15 - 15 / saca Second Player / [('1', '6', '4'), ('2', '3', '3')] | {'sa': 1, 'sb': 0, 'ga': 3, 'gb': 3, 'xa': 1, 'xb': 1, 'a_saca': False, 'previos': (6, 4), 'mejor_de': 3} |

get_live_odds: dict con 59 elementos.
Ejemplo:
```
{
 "event_key": 12166178,
 "event_date": "2026-09-30",
 "event_time": "11:10",
 "first_player_key": 410,
 "first_player_dp1_key": null,
 "first_player_dp2_key": null,
 "second_player_key": 379,
 "second_player_dp1_key": null,
 "second_player_dp2_key": null,
 "event_game_result": "0 - 0",
 "event_serve": "Second Player",
 "event_winner": null,
 "event_status": "Set 2",
 "event_type_type": "Challenger Men Singles",
 "tournament_name": "Mouilleron-Le-Captif",
 "tournament_key": 2420,
 "tournament_round": "Mouilleron-Le-Captif - 1/16-finals",
 "tournament_season": "2026",
 "event_live": "11:10",
 "event_first_player_logo": "https://api.api-tennis.com/logo-tennis/410_l-broady.jpg",
 "event_second_player_logo": "https://api.api-tennis.com/logo-tennis/379_d-stricker.jpg",
 "event_qualification": "False",
 "live_odds": [
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "Yes",
   "type": "Over",
   "value": "17",
   "handicap": "12.5",
   "upd": "2026-09-30 11:47:27"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "Yes",
   "type": "Under",
   "value": "1.025",
   "handicap": "12.5",
   "upd": "2026-09-30 11:47:27"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "Yes",
   "type": "Over",
   "value": "11",
   "handicap": "10.5",
   "upd": "2026-09-30 11:47:27"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "Yes",
   "type": "Under",
   "value": "1.05",
   "handicap": "10.5",
   "upd": "2026-09-30 11:47:27"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "No",
   "type": "Over",
   "value": "1.012",
   "handicap": "9.5",
   "upd": "2026-09-30 11:37:28"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "No",
   "type": "Under",
   "value": "23",
   "handicap": "9.5",
   "upd": "2026-09-30 11:37:28"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "No",
   "type": "Over",
   "value": "1",
   "handicap": "8.5",
   "upd": "2026-09-30 11:27:27"
  },
  {
   "odd_name": "Total Games in Set 1",
   "suspended": "No",
   "type": "Under",
   "value": "101",
   "handicap": "8.5",
   "upd": "2026-09-30 11:27:27"
  },
  {
   "odd_name": "Match Result and Total Games",
   "suspended": "No",
   "type": "2/o",
   "value": "2.4",
   "handicap": "22.5",
   "upd": "2026-09-30 12:01:48"
  },
  {
   "odd_name": "Match Result and Total Games",
   "suspended": "No",
   "type": "2/u",
   "value": "2",
   "handicap": "22.5",
   "upd": "2026-09-30 12:01:48"
  },
  {
   "odd_name": "Match Result and Total Games",
   "suspended": "No",
   "type": "1/o",
   "value": "9",
   "handicap": "30.5",
   "upd": "2026-09-30 12:00:08"
  },
  {
   "odd_name": "Match Result and Total Games",
   "suspended": "No",
   "type": "1/u",
   "value": "9.5",
   "handicap": "30.5",
   "upd": "2026-09-30 12:00:08"
  },
  {
   "odd_name": "Player 2 To_Win from Behind (Sets)",
   "suspended": "No",
   "type": "Yes",
   "value": "41",
   "handicap": null,
   "upd": "2026-09-30 11:47:27"
  },
  {
   "odd_name":
```
