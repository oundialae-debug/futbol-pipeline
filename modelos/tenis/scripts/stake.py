"""
Enlace a Stake para los avisos (30/09/2026). La dirección de un PARTIDO lleva un número interno de
Stake (…/46943897-alex-de-minaur-mariano-navone) que no se puede sacar desde aquí (Stake bloquea a
GitHub y al contenedor), pero la del TORNEO sí se puede montar. Patrones vistos con direcciones
reales que pasó el usuario (y la de ATP Pekín probada por él):
  ATP        tennis/atp/atp-beijing-china-men-singles
  Challenger tennis/challenger/atp-challenger-bari-italy-men-singles
  WTA        tennis/wta/wta-beijing-china-women-singles
Stake pone ciudad Y país; la API a menudo solo da la ciudad ("Beijing", "Curitiba"), así que el país
sale de PAISES. Sin país conocido, o en circuitos sin patrón visto (WTA 125, ITF), se da la página
del circuito o la de tenis: mejor un enlace más general que uno roto.
"""
import re
import unicodedata

BASE = "https://stake.com/es/sports/tennis"
PAISES = {
    # circuito ATP/WTA
    "beijing": "china", "shanghai": "china", "wuhan": "china", "chengdu": "china", "hangzhou": "china",
    "zhuhai": "china", "guangzhou": "china", "ningbo": "china", "shenzhen": "china", "tokyo": "japan",
    "osaka": "japan", "seoul": "south-korea", "hong-kong": "hong-kong", "almaty": "kazakhstan",
    "astana": "kazakhstan", "basel": "switzerland", "gstaad": "switzerland", "geneva": "switzerland",
    "vienna": "austria", "kitzbuhel": "austria", "linz": "austria", "paris": "france", "lyon": "france",
    "marseille": "france", "montpellier": "france", "metz": "france", "strasbourg": "france", "rouen": "france",
    "antwerp": "belgium", "stockholm": "sweden", "bastad": "sweden", "stuttgart": "germany",
    "munich": "germany", "berlin": "germany", "hamburg": "germany", "halle": "germany", "bad-homburg": "germany",
    "madrid": "spain", "barcelona": "spain", "mallorca": "spain", "rome": "italy", "palermo": "italy",
    "parma": "italy", "turin": "italy", "london": "great-britain", "queens": "great-britain",
    "eastbourne": "great-britain", "nottingham": "great-britain", "birmingham": "great-britain",
    "wimbledon": "great-britain", "s-hertogenbosch": "netherlands", "rotterdam": "netherlands",
    "estoril": "portugal", "lisbon": "portugal", "porto": "portugal", "umag": "croatia",
    "belgrade": "serbia", "gdansk": "poland", "warsaw": "poland", "prague": "czech-republic",
    "ostrava": "czech-republic", "cluj-napoca": "romania", "bucharest": "romania", "iasi": "romania",
    "doha": "qatar", "dubai": "united-arab-emirates", "abu-dhabi": "united-arab-emirates",
    "riyadh": "saudi-arabia", "adelaide": "australia", "brisbane": "australia", "melbourne": "australia",
    "sydney": "australia", "hobart": "australia", "perth": "australia", "auckland": "new-zealand",
    "buenos-aires": "argentina", "cordoba": "argentina", "rio-de-janeiro": "brazil", "sao-paulo": "brazil",
    "curitiba": "brazil", "santiago": "chile", "acapulco": "mexico", "los-cabos": "mexico",
    "guadalajara": "mexico", "monterrey": "mexico", "merida": "mexico", "bogota": "colombia",
    "indian-wells": "usa", "miami": "usa", "cincinnati": "usa", "washington": "usa", "new-york": "usa",
    "atlanta": "usa", "winston-salem": "usa", "dallas": "usa", "delray-beach": "usa", "houston": "usa",
    "charleston": "usa", "austin": "usa", "san-diego": "usa", "columbus": "usa", "cleveland": "usa",
    "chicago": "usa", "toronto": "canada", "montreal": "canada", "vancouver": "canada",
    "granby": "canada", "jingshan": "china", "shenzhen-luohu": "china", "mouilleron-le-captif": "france",
    "orleans": "france", "brest": "france", "bari": "italy", "genoa": "italy", "naples": "italy",
    "florence": "italy", "bergamo": "italy", "biella": "italy", "szczecin": "poland", "istanbul": "turkey",
    "antalya": "turkey", "adana": "turkey", "tashkent": "uzbekistan", "sofia": "bulgaria",
    "tenerife": "spain", "alicante": "spain", "valencia": "spain", "sevilla": "spain", "seville": "spain",
}


def _slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def enlace(tipo, torneo):
    """Página del torneo en Stake si se puede montar con seguridad; si no, la del circuito o la de tenis."""
    nombre = str(torneo).split(" - ")[0]                       # fuera " - Qualification"
    m = re.match(r"(.*?)\s*\((.*)\)\s*$", nombre)              # "Bari (Italy)"
    ciudad, pais = (m.group(1), _slug(m.group(2))) if m else (nombre, None)
    ciudad = _slug(ciudad)
    pais = pais or PAISES.get(ciudad)
    circ = {"Atp Singles": ("atp", "atp-{c}-{p}-men-singles"),
            "Wta Singles": ("wta", "wta-{c}-{p}-women-singles"),
            "Challenger Men Singles": ("challenger", "atp-challenger-{c}-{p}-men-singles")}.get(tipo)
    if circ is None:
        return BASE
    if not pais:
        return f"{BASE}/{circ[0]}"
    return f"{BASE}/{circ[0]}/" + circ[1].format(c=ciudad, p=pais)


if __name__ == "__main__":
    for t, n in [("Atp Singles", "Beijing"), ("Challenger Men Singles", "Bari (Italy) - Qualification"),
                 ("Wta Singles", "Beijing"), ("Challenger Men Singles", "Curitiba"), ("Itf Men Singles", "M15 Telavi 2 (Georgia)"),
                 ("Challenger Men Singles", "Xyz")]:
        print(t, n, "->", enlace(t, n))
