# Ficheros de tennis-data.co.uk, bajados A MANO por el usuario

tennis-data.co.uk limita su uso a particulares y bloquea a los agentes de IA
en su robots.txt, así que Claude no los descarga. Bájalos desde
http://www.tennis-data.co.uk/alldata.php y déjalos en esta carpeta tal cual:

- ATP: un fichero por año (`2024.xlsx`, `2025.xlsx`, ...). Renómbralos a
  `atp_2024.xlsx`, `atp_2025.xlsx`...
- WTA: igual, `wta_2024.xlsx`, `wta_2025.xlsx`...
- Antes de 2013 son `.xls` (vale igual: `atp_2010.xls`).
- Si vienen en .zip, descomprime primero.

Luego: `python3 modelos/tenis/scripts/procesar_tennis_data.py`.
