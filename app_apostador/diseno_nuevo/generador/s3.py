from common import *

def team_tabs(active, names):
    parts = ['<nav aria-label="Sections" style="display: flex; gap: 24px; padding: 0 16px; border-bottom: 1px solid #232838">']
    for n in names:
        on = n == active
        parts.append('<a href="#" %s style="height: 46px; display: flex; align-items: center; border-bottom: 3px solid %s; color: %s; font-size: 14px; font-weight: 700; white-space: nowrap">%s</a>' % ('aria-current="page"' if on else '', "#C8FF3D" if on else "transparent", "#F1F3F8" if on else "#8E96AA", n))
    parts.append('</nav>')
    return "\n".join(parts)

# ---------------------------------------------------------------- TEAM
BODY = r'''
<div style="position: relative; width: 390px; height: 2040px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #2F63D8; opacity: 0.4; filter: blur(70px)"></span>
<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 0 4px">
<a href="Main.dc.html" aria-label="Back" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>
<span style="flex-grow: 1"></span>
<button aria-label="Share" style="width: 44px; height: 44px; border: none; background: transparent; color: #F1F3F8"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V4M8 8l4-4 4 4M5 13v6h14v-6"></path></svg></button>
</header>
<div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 4px 16px 18px 16px">
<span style="width: 84px; height: 84px; border-radius: 50%; background: #2F63D8; color: #FFFFFF; font-weight: 800; font-size: 22px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px rgba(255,255,255,0.2)">RIV</span>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 34px; line-height: 1">Riverton</span>
<span style="font-size: 13px; color: #C6CBD8">Coastal League · 3rd · Founded 1911</span>
<div style="display: flex; gap: 8px; margin-top: 4px">
<button style="height: 40px; padding: 0 20px; border: none; border-radius: 20px; background: #C8FF3D; color: #0A0C11; font-size: 14px; font-weight: 800">Following</button>
<button aria-label="Alerts" style="width: 40px; height: 40px; border: 1px solid #3A4256; border-radius: 20px; background: transparent; color: #F1F3F8; display: flex; align-items: center; justify-content: center"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16V11a6 6 0 0112 0v5l1.5 2h-15zM10 20a2 2 0 004 0"></path></svg></button>
</div>
</div>
</div>

@@TABS@@

<a href="Partido.dc.html" style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: center"><span style="font-size: 12px; font-weight: 700; letter-spacing: 0.5px; color: #8E96AA">NEXT MATCH</span><span style="padding: 3px 10px; border-radius: 10px; background: #1E2A66; color: #A9B8FF; font-size: 12px; font-weight: 700">Sat 19 · 18:30</span></div>
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 40px; height: 40px; border-radius: 50%; background: #2F63D8; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center">RIV</span><span style="font-size: 15px; font-weight: 700">Riverton</span></div>
<span style="font-size: 13px; color: #8E96AA">vs</span>
<div style="display: flex; align-items: center; gap: 10px"><span style="font-size: 15px; font-weight: 700">Oakmont</span><span style="width: 40px; height: 40px; border-radius: 50%; background: #F07A2A; color: #0A0C11; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center">OAK</span></div>
</div>
<div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 2px"><span style="width: 58%; background: #2F63D8"></span><span style="width: 24%; background: #3A4256"></span><span style="width: 18%; background: #F07A2A"></span></div>
<div style="display: flex; justify-content: space-between; font-size: 12px; color: #C6CBD8"><span>58% Riverton</span><span>24% draw</span><span>18% Oakmont</span></div>
</a>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Form</span><span style="font-size: 12px; color: #8E96AA">latest on the right</span></div>
<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px">
<sc-for list="{{forma}}" as="f" hint-placeholder-count="5">
<div style="display: flex; flex-direction: column; align-items: center; gap: 5px"><span style="width: 100%; height: 44px; border-radius: 12px; background: {{f.bg}}; color: {{f.fg}}; display: flex; flex-direction: column; align-items: center; justify-content: center"><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 17px; line-height: 1">{{f.marcador}}</span></span><span style="font-size: 10px; color: #8E96AA">{{f.rival}}</span></div>
</sc-for>
</div>
</section>

<section style="margin: 0 12px; border-radius: 24px; background: #12151C; border: 1px solid #232838; overflow: hidden">
<div style="display: flex; justify-content: space-between; align-items: baseline; padding: 16px 16px 8px 16px"><span style="font-size: 16px; font-weight: 700">Table</span><span style="font-size: 12px; color: #8FA2FF; font-weight: 600">Full table</span></div>
<div style="display: flex; align-items: center; gap: 8px; padding: 0 16px 6px 16px; font-size: 10px; letter-spacing: 0.5px; color: #8E96AA"><span style="width: 22px">#</span><span style="flex-grow: 1">TEAM</span><span style="width: 24px; text-align: right">GD</span><span style="width: 26px; text-align: right">PTS</span><span style="width: 62px; text-align: center">STRENGTH</span></div>
<sc-for list="{{tabla}}" as="t" hint-placeholder-count="5">
<div style="display: flex; align-items: center; gap: 8px; min-height: 46px; padding: 0 16px; background: {{t.fondo}}; border-top: 1px solid #1E2330">
<span style="width: 22px; font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 15px; color: {{t.posColor}}">{{t.pos}}</span>
<span style="width: 22px; height: 22px; border-radius: 50%; background: {{t.color}}; flex-shrink: 0"></span>
<span style="flex-grow: 1; font-size: 14px; font-weight: {{t.peso}}">{{t.equipo}}</span>
<span style="width: 24px; text-align: right; font-size: 13px; color: #C6CBD8">{{t.dg}}</span>
<span style="width: 26px; text-align: right; font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 15px">{{t.pts}}</span>
<span style="width: 62px; display: flex; justify-content: center"><span style="padding: 2px 8px; border-radius: 8px; background: {{t.tagBg}}; color: {{t.tagFg}}; font-size: 11px; font-weight: 700">{{t.tag}}</span></span>
</div>
</sc-for>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Chances created vs conceded</span><span style="font-size: 12px; color: #8E96AA">xG, last 8</span></div>
<div style="display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 6px">
<sc-for list="{{xg}}" as="x" hint-placeholder-count="8">
<div style="display: flex; flex-direction: column; align-items: center; gap: 4px">
<div style="height: 60px; width: 100%; display: flex; align-items: flex-end"><span style="width: 100%; height: {{x.up}}px; border-radius: 4px 4px 0 0; background: #2F63D8"></span></div>
<div style="height: 1px; width: 100%; background: #2A3040"></div>
<div style="height: 60px; width: 100%; display: flex; align-items: flex-start"><span style="width: 100%; height: {{x.down}}px; border-radius: 0 0 4px 4px; background: #E0424B"></span></div>
</div>
</sc-for>
</div>
<div style="display: flex; gap: 16px; font-size: 12px; color: #C6CBD8"><span style="display: flex; align-items: center; gap: 6px"><span style="width: 10px; height: 10px; border-radius: 3px; background: #2F63D8"></span>Created</span><span style="display: flex; align-items: center; gap: 6px"><span style="width: 10px; height: 10px; border-radius: 3px; background: #E0424B"></span>Conceded</span></div>
</section>

<section style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline; padding: 0 16px"><span style="font-size: 18px; font-weight: 700">Top players</span><span style="font-size: 13px; font-weight: 600; color: #8FA2FF">Squad</span></div>
<div style="display: flex; gap: 10px; padding: 0 16px; overflow: hidden">
<sc-for list="{{jugadores}}" as="j" hint-placeholder-count="3">
<a href="Jugador.dc.html" style="flex-shrink: 0; width: 148px; box-sizing: border-box; padding: 14px; border-radius: 22px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center">
<span style="position: relative; width: 60px; height: 60px; border-radius: 50%; background: #1A1E28; font-weight: 800; font-size: 18px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 3px #2F63D8">{{j.ini}}<span style="position: absolute; right: -8px; bottom: -4px; padding: 1px 6px; border-radius: 8px; background: {{j.rbg}}; color: {{j.rfg}}; font-size: 11px; font-weight: 800">{{j.rating}}</span></span>
<span style="font-size: 14px; font-weight: 700">{{j.nombre}}</span>
<span style="font-size: 12px; color: #8E96AA">{{j.pos}}</span>
<span style="padding: 3px 10px; border-radius: 9px; background: #1E2330; font-size: 12px; font-weight: 700">{{j.dato}}</span>
</a>
</sc-for>
</div>
</section>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    const R = (r, rival, gf, gc) => ({ bg: r === 'W' ? '#C8FF3D' : r === 'D' ? '#3A4256' : '#FF8A3D', fg: r === 'D' ? '#FFFFFF' : '#0A0C11', rival, marcador: gf + '-' + gc });
    const forma = [R('W', 'CAL', 3, 1), R('W', 'NOR', 2, 0), R('D', 'BAY', 1, 1), R('W', 'HAR', 2, 1), R('L', 'OAK', 0, 2)];
    const tagOf = (d) => d >= 3 ? ['Underrated', '#172A66', '#A9B8FF'] : d <= -3 ? ['Overrated', '#3A2412', '#FFB27A'] : ['Fair', '#1E2330', '#C6CBD8'];
    const filas = [
      [2, 'Calder City', '#E8ECF3', '+9', 19, 1], [3, 'Riverton', '#2F63D8', '+7', 18, 2], [4, 'Bayfield', '#F2C230', '+3', 17, 8],
      [5, 'Northgate', '#2FA36B', '+2', 16, 3], [6, 'Oakmont', '#F07A2A', '+1', 15, 4]
    ];
    const tabla = filas.map(([pos, equipo, color, dg, pts, fuerza], i) => {
      const d = pos - fuerza, tg = tagOf(d), yo = equipo === 'Riverton';
      return { pos, equipo, color, dg, pts, fondo: yo ? '#182042' : 'transparent', peso: yo ? 700 : 500, posColor: yo ? '#C8FF3D' : '#F1F3F8', tag: tg[0], tagBg: tg[1], tagFg: tg[2] };
    });
    const up = [30, 46, 22, 38, 54, 28, 42, 50], down = [18, 10, 26, 14, 20, 34, 12, 16];
    const xg = up.map((u, i) => ({ up: u, down: down[i] }));
    const rc = (r) => r >= 7.5 ? ['#C8FF3D', '#0A0C11'] : ['#3A4256', '#FFFFFF'];
    const J = (ini, nombre, pos, rating, dato) => ({ ini, nombre, pos, rating: rating.toFixed(1), dato, rbg: rc(rating)[0], rfg: rc(rating)[1] });
    const jugadores = [J('OK', 'Okafor', 'Forward', 8.1, '9 goals'), J('LI', 'Lindqvist', 'Midfielder', 7.6, '6 assists'), J('RO', 'Roca', 'Defender', 7.3, '4 clean sheets')];
    return { forma, tabla, xg, jugadores };
  }
}'''
page("Equipo.dc.html", "Team", 390, 2040, BODY, JS, nav_active="e", tabs_active=None)
# replace the tabs placeholder for team
p = os.path.join(OUT, "Equipo.dc.html")
s = open(p).read().replace("@@TABS@@", team_tabs("Overview", ["Overview", "Table", "Squad", "Stats", "Fixtures"]))
open(p, "w").write(s)

# ---------------------------------------------------------------- PLAYER
BODY = r'''
<div style="position: relative; width: 390px; height: 2200px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #2F63D8; opacity: 0.4; filter: blur(70px)"></span>
<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 0 4px">
<a href="Equipo.dc.html" aria-label="Back" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>
<span style="flex-grow: 1"></span>
<button aria-label="Follow player" style="width: 44px; height: 44px; border: none; background: transparent; color: #F1F3F8"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.6-7 10-7 10z"></path></svg></button>
</header>
<div style="position: relative; display: flex; align-items: center; gap: 16px; padding: 6px 16px 18px 16px">
<span style="position: relative; width: 96px; height: 96px; flex-shrink: 0; border-radius: 50%; background: #1A1E28; font-weight: 800; font-size: 30px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px #2F63D8">OK<span style="position: absolute; right: -6px; bottom: -2px; padding: 3px 10px; border-radius: 12px; background: #C8FF3D; color: #0A0C11; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">8.1</span></span>
<div style="display: flex; flex-direction: column; gap: 6px">
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 34px; line-height: 1">Emeka Okafor</span>
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 22px; height: 22px; border-radius: 50%; background: #2F63D8; font-size: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center">RIV</span><span style="font-size: 13px; color: #C6CBD8">Riverton · #9</span></div>
<div style="display: flex; gap: 6px"><span style="padding: 3px 10px; border-radius: 9px; background: #1E2330; font-size: 12px; font-weight: 700">Forward</span><span style="padding: 3px 10px; border-radius: 9px; background: #1E2330; font-size: 12px; font-weight: 700">Right foot</span></div>
</div>
</div>
</div>

<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding: 0 12px">
<div style="padding: 10px 6px; border-radius: 16px; background: #12151C; border: 1px solid #232838; text-align: center"><span style="display: block; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">26</span><span style="font-size: 11px; color: #8E96AA">Age</span></div>
<div style="padding: 10px 6px; border-radius: 16px; background: #12151C; border: 1px solid #232838; text-align: center"><span style="display: block; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">184</span><span style="font-size: 11px; color: #8E96AA">cm</span></div>
<div style="padding: 10px 6px; border-radius: 16px; background: #12151C; border: 1px solid #232838; text-align: center"><span style="display: block; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">NGA</span><span style="font-size: 11px; color: #8E96AA">Country</span></div>
<div style="padding: 10px 6px; border-radius: 16px; background: #12151C; border: 1px solid #232838; text-align: center"><span style="display: block; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">€38M</span><span style="font-size: 11px; color: #8E96AA">Value</span></div>
</div>

@@TABS@@

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">This season</span><span style="font-size: 12px; color: #8E96AA">Coastal League</span></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<sc-for list="{{resumen}}" as="r" hint-placeholder-count="6">
<div style="padding: 12px; border-radius: 16px; background: #1A1E28"><span style="display: block; font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 26px; line-height: 1.1; color: {{r.color}}">{{r.valor}}</span><span style="font-size: 12px; color: #8E96AA">{{r.nombre}}</span></div>
</sc-for>
</div>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Match ratings</span><span style="font-size: 12px; color: #8E96AA">last 10</span></div>
<div style="display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 4px; align-items: end; height: 132px">
<sc-for list="{{notas}}" as="n" hint-placeholder-count="10">
<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px; height: 100%"><span style="font-size: 10px; font-weight: 700; color: {{n.color}}">{{n.txt}}</span><span style="width: 100%; height: {{n.h}}px; border-radius: 5px; background: {{n.color}}"></span></div>
</sc-for>
</div>
<div style="display: flex; justify-content: space-between; font-size: 11px; color: #8E96AA"><span>oldest</span><span>latest</span></div>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 16px; font-weight: 700">Compared with forwards</span><span style="font-size: 12px; color: #8E96AA">percentile in Coastal League, per 90</span></div>
<sc-for list="{{percentiles}}" as="p" hint-placeholder-count="6">
<div style="display: flex; align-items: center; gap: 10px">
<span style="width: 108px; font-size: 13px; color: #C6CBD8">{{p.nombre}}</span>
<div style="flex-grow: 1; height: 10px; border-radius: 5px; background: #1E2330"><div style="width: {{p.pct}}%; height: 10px; border-radius: 5px; background: {{p.color}}"></div></div>
<span style="width: 30px; text-align: right; font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 15px">{{p.pct}}</span>
</div>
</sc-for>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Shot map</span><span style="font-size: 12px; color: #8E96AA">21 shots · 9 goals</span></div>
<svg width="342" height="200" viewBox="0 0 342 200" role="img" aria-label="Shot map of Okafor: 21 shots, 9 goals" style="display: block; max-width: 100%; border-radius: 16px; background: #0F1B15">
<rect x="6" y="6" width="330" height="188" rx="4" fill="none" stroke="#25392E" stroke-width="2"></rect>
<rect x="96" y="6" width="150" height="76" fill="none" stroke="#25392E" stroke-width="2"></rect>
<rect x="136" y="6" width="70" height="28" fill="none" stroke="#25392E" stroke-width="2"></rect>
<path d="M136 82 A 36 36 0 0 0 206 82" fill="none" stroke="#25392E" stroke-width="2"></path>
<circle cx="171" cy="60" r="2.5" fill="#25392E"></circle>
<circle cx="171" cy="26" r="10" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="150" cy="44" r="12" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="192" cy="40" r="9" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="164" cy="60" r="8" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="182" cy="66" r="7" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="130" cy="56" r="6" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="214" cy="52" r="6" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="171" cy="80" r="6" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="150" cy="30" r="5" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="120" cy="84" r="5" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="226" cy="90" r="5" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="171" cy="102" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="140" cy="112" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="200" cy="116" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="100" cy="100" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="250" cy="110" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="171" cy="136" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="120" cy="140" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="220" cy="146" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="171" cy="166" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="90" cy="70" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
</svg>
</section>

<section style="margin: 0 12px; border-radius: 24px; background: #12151C; border: 1px solid #232838; overflow: hidden">
<div style="padding: 16px 16px 8px 16px"><span style="font-size: 16px; font-weight: 700">Latest matches</span></div>
<sc-for list="{{partidos}}" as="p" hint-placeholder-count="4">
<div style="display: flex; align-items: center; gap: 12px; min-height: 54px; padding: 0 16px; border-top: 1px solid #1E2330">
<span style="width: 40px; font-size: 12px; color: #8E96AA">{{p.fecha}}</span>
<span style="width: 24px; height: 24px; border-radius: 50%; background: {{p.color}}; flex-shrink: 0"></span>
<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 600">{{p.rival}}</span><span style="font-size: 12px; color: #8E96AA">{{p.res}} · {{p.min}}'</span></div>
<span style="font-size: 12px; font-weight: 600; color: #C6CBD8">{{p.g}}</span>
<span style="padding: 2px 8px; border-radius: 8px; background: {{p.rbg}}; color: {{p.rfg}}; font-size: 12px; font-weight: 800">{{p.nota}}</span>
</div>
</sc-for>
</section>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    const col = (r) => r >= 7.5 ? '#C8FF3D' : r >= 6.5 ? '#8E96AA' : '#FF8A3D';
    const resumen = [['Apps', '14', '#F1F3F8'], ['Minutes', '1,142', '#F1F3F8'], ['Goals', '9', '#C8FF3D'], ['Assists', '3', '#F1F3F8'], ['xG', '7.4', '#8FA2FF'], ['Rating', '7.62', '#C8FF3D']].map(([nombre, valor, color]) => ({ nombre, valor, color }));
    const notas = [6.4, 7.1, 8.4, 6.8, 7.9, 6.2, 8.1, 7.6, 9.0, 8.6].map((r) => ({ txt: r.toFixed(1), h: Math.round((r - 4) / 6 * 90), color: col(r) }));
    const percentiles = [['Goals', 96], ['Expected goals', 91], ['Shots on target', 84], ['Dribbles', 62], ['Key passes', 41], ['Aerial duels won', 28]].map(([nombre, pct]) => ({ nombre, pct, color: pct >= 75 ? '#C8FF3D' : pct >= 40 ? '#4A63FF' : '#FF8A3D' }));
    const partidos = [
      { fecha: '16 Sep', rival: 'Ashford Utd', res: 'Live 2-1', min: 67, g: '1 goal', nota: '8.6', color: '#E0424B' },
      { fecha: '12 Sep', rival: 'Calder City', res: 'W 3-1', min: 90, g: '1 goal', nota: '9.0', color: '#E8ECF3' },
      { fecha: '05 Sep', rival: 'Northgate', res: 'W 2-0', min: 82, g: '—', nota: '7.6', color: '#2FA36B' },
      { fecha: '29 Aug', rival: 'Bayfield', res: 'D 1-1', min: 90, g: '1 goal', nota: '8.1', color: '#F2C230' }
    ].map((p) => ({ ...p, rbg: parseFloat(p.nota) >= 7.5 ? '#C8FF3D' : '#3A4256', rfg: parseFloat(p.nota) >= 7.5 ? '#0A0C11' : '#FFFFFF' }));
    return { resumen, notas, percentiles, partidos };
  }
}'''
page("Jugador.dc.html", "Player", 390, 2200, BODY, JS, nav_active="f", tabs_active=None)
p = os.path.join(OUT, "Jugador.dc.html")
s = open(p).read().replace("@@TABS@@", team_tabs("Season", ["Season", "Matches", "Stats", "Career"]))
open(p, "w").write(s)

# ---------------------------------------------------------------- TIPS
BODY = r'''
<div style="position: relative; width: 390px; height: 1900px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px">
<span style="flex-grow: 1; font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 32px">Tips</span>
<button aria-label="Filters" style="width: 44px; height: 44px; border: none; border-radius: 22px; background: #161A23; color: #F1F3F8; display: flex; align-items: center; justify-content: center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 6h16M7 12h10M10 18h4"></path></svg></button>
</header>

<div style="display: flex; gap: 8px; padding: 0 16px">
<sc-for list="{{filtros}}" as="f" hint-placeholder-count="4">
<button style="height: 38px; padding: 0 16px; border-radius: 19px; border: 1px solid {{f.borde}}; background: {{f.fondo}}; color: #FFFFFF; font-size: 13px; font-weight: 700; white-space: nowrap">{{f.nombre}}</button>
</sc-for>
</div>

<section style="position: relative; margin: 0 12px; padding: 18px; border-radius: 28px; background: #12151C; border: 1px solid #262C3B; overflow: hidden; display: flex; flex-direction: column; gap: 14px">
<span style="position: absolute; right: -50px; top: -60px; width: 200px; height: 200px; border-radius: 50%; background: #C8FF3D; opacity: 0.22; filter: blur(50px)"></span>
<div style="position: relative; display: flex; justify-content: space-between; align-items: center"><span style="padding: 4px 12px; border-radius: 12px; background: #C8FF3D; color: #0A0C11; font-size: 12px; font-weight: 800; letter-spacing: 0.4px">TOP PICK</span><span style="font-size: 12px; color: #C6CBD8">Wed 16 · 18:30</span></div>
<div style="position: relative; display: flex; align-items: center; gap: 16px">
<svg width="112" height="112" viewBox="0 0 112 112" role="img" aria-label="88 percent" style="flex-shrink: 0">
<circle cx="56" cy="56" r="46" fill="none" stroke="#232838" stroke-width="12"></circle>
<circle cx="56" cy="56" r="46" fill="none" stroke="#C8FF3D" stroke-width="12" stroke-linecap="round" stroke-dasharray="254 289" transform="rotate(-90 56 56)"></circle>
<text x="56" y="62" text-anchor="middle" fill="#F1F3F8" font-family="Archivo, sans-serif" font-weight="800" font-size="30">88%</text>
</svg>
<div style="display: flex; flex-direction: column; gap: 6px">
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 28px; line-height: 1.05">Over 1.5 goals</span>
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 22px; height: 22px; border-radius: 50%; background: #2F63D8; font-size: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center">RIV</span><span style="font-size: 13px; font-weight: 600">Riverton – Ashford Utd</span><span style="width: 22px; height: 22px; border-radius: 50%; background: #E0424B; font-size: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center">ASH</span></div>
<span style="font-size: 13px; color: #C6CBD8">Fair odds <b style="color: #F1F3F8; font-family: 'Archivo', sans-serif">1.14</b></span>
</div>
</div>
<div style="position: relative; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: #1A1E28"><span style="display: block; font-size: 11px; color: #8E96AA">Bookmakers hit</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 24px">78%</span><span style="display: block; font-size: 11px; color: #8E96AA">on this market</span></div>
<div style="padding: 12px; border-radius: 16px; background: #1A1E28"><span style="display: block; font-size: 11px; color: #8E96AA">Our tips hit</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 24px; color: #C8FF3D">76%</span><span style="display: block; font-size: 11px; color: #8E96AA">when we said 75–80%</span></div>
</div>
<div style="position: relative; display: flex; align-items: center; gap: 8px; padding: 6px 6px 6px 14px; border-radius: 16px; background: #0A0C11; border: 1px solid #2A3040">
<label for="odds" style="flex-grow: 1; font-size: 13px; color: #C6CBD8">Your bookmaker pays</label>
<input id="odds" type="text" inputmode="decimal" value="1.20" style="width: 72px; height: 40px; box-sizing: border-box; border: none; border-radius: 12px; background: #1A1E28; color: #F1F3F8; text-align: center; font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 18px">
<span style="height: 40px; padding: 0 14px; border-radius: 12px; background: #C8FF3D; color: #0A0C11; font-size: 13px; font-weight: 800; display: flex; align-items: center">Good price +5%</span>
</div>
</section>

<div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px 0 16px"><span style="font-size: 18px; font-weight: 700">More tips</span><span style="font-size: 12px; color: #8E96AA">sorted by confidence</span></div>

<sc-for list="{{tips}}" as="t" hint-placeholder-count="5">
<a href="#" style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: #12151C; border: 1px solid #232838; display: flex; align-items: center; gap: 14px">
<div style="display: flex; flex-direction: column; gap: 6px; flex-grow: 1; min-width: 0">
<span style="font-size: 12px; color: #8E96AA">{{t.liga}} · {{t.hora}}</span>
<span style="font-size: 16px; font-weight: 700">{{t.mercado}}</span>
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 20px; height: 20px; border-radius: 50%; background: {{t.cl}}; color: {{t.tl}}; font-size: 7px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{t.il}}</span><span style="font-size: 13px; color: #C6CBD8">{{t.partido}}</span><span style="width: 20px; height: 20px; border-radius: 50%; background: {{t.cv}}; color: {{t.tv}}; font-size: 7px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{t.iv}}</span></div>
<div style="display: flex; gap: 6px"><span style="padding: 2px 9px; border-radius: 9px; background: #1E2330; color: #C6CBD8; font-size: 11px; font-weight: 700">fair {{t.justa}}</span><span style="padding: 2px 9px; border-radius: 9px; background: {{t.tagBg}}; color: {{t.tagFg}}; font-size: 11px; font-weight: 700">{{t.tag}}</span></div>
</div>
<div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px"><span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 36px; line-height: 1; color: #C8FF3D">{{t.pct}}<span style="font-size: 18px">%</span></span><span style="font-size: 11px; color: #8E96AA">books {{t.casa}}%</span></div>
</a>
</sc-for>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Our track record</span><span style="font-size: 12px; color: #8E96AA">last 30 days · sample</span></div>
<div style="display: flex; align-items: baseline; gap: 10px"><span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 44px; line-height: 1">67%</span><span style="font-size: 13px; color: #C6CBD8">of 142 tips were right</span></div>
<div style="display: grid; grid-template-columns: repeat(15, minmax(0, 1fr)); gap: 4px; align-items: end; height: 56px">
<sc-for list="{{racha}}" as="r" hint-placeholder-count="15">
<span style="height: {{r.h}}px; border-radius: 3px; background: {{r.color}}"></span>
</sc-for>
</div>
<span style="font-size: 12px; color: #8E96AA">Each bar is one day. Blue days beat the 60% mark.</span>
</section>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    const filtros = ['Today', 'Goals', 'Result', 'Cards'].map((nombre, i) => ({ nombre, fondo: i === 0 ? '#4A63FF' : '#12151C', borde: i === 0 ? '#4A63FF' : '#262C3B' }));
    const E = { RIV: ['#2F63D8', '#FFFFFF'], ASH: ['#E0424B', '#FFFFFF'], CAL: ['#E8ECF3', '#0A0C11'], BAY: ['#F2C230', '#0A0C11'], NOR: ['#2FA36B', '#FFFFFF'], HAR: ['#9B4FD0', '#FFFFFF'], VAL: ['#E8ECF3', '#0A0C11'], LAK: ['#33B5E5', '#0A0C11'] };
    const T = (liga, hora, mercado, il, iv, partido, pct, casa, tag) => {
      const t = { good: ['#1F3A16', '#C8FF3D'], watch: ['#3A2412', '#FFB27A'], plain: ['#1E2330', '#C6CBD8'] }[tag[0]];
      return { liga, hora, mercado, il, iv, partido, pct, casa, justa: (100 / pct).toFixed(2), tag: tag[1], tagBg: t[0], tagFg: t[1], cl: E[il][0], tl: E[il][1], cv: E[iv][0], tv: E[iv][1] };
    };
    const tips = [
      T('Metro Cup', '21:00', 'Under 3.5 goals', 'VAL', 'LAK', 'Vale – Lakeside', 79, 62, ['good', 'Big gap vs books']),
      T('Coastal League', '18:30', 'Calder City to win', 'CAL', 'BAY', 'Calder – Bayfield', 48, 47, ['plain', 'In line']),
      T('Coastal League', '20:45', 'Both teams score', 'NOR', 'HAR', 'Northgate – Harbor', 64, 59, ['good', 'Above books']),
      T('Coastal League', '18:30', 'Over 2.5 goals', 'CAL', 'BAY', 'Calder – Bayfield', 61, 61, ['plain', 'In line']),
      T('Metro Cup', '21:00', 'Over 4.5 cards', 'VAL', 'LAK', 'Vale – Lakeside', 52, 47, ['watch', 'Strict referee'])
    ];
    const vals = [55, 70, 40, 62, 50, 74, 68, 45, 72, 58, 66, 80, 60, 52, 76];
    const racha = vals.map((v) => ({ h: Math.round(v / 100 * 56), color: v >= 60 ? '#4A63FF' : '#3A4256' }));
    return { filtros, tips, racha };
  }
}'''
BODY = BODY.replace("#12151C", "#12151C")
page("Tips.dc.html", "Tips", 390, 1900, BODY, JS, nav_active="t")
print("s3 ok")
