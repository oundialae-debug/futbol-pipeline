from common import *

# ---------------------------------------------------------------- STATS
BODY = r'''
<div style="position: relative; width: 390px; height: 2140px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: -60px; top: -80px; width: 220px; height: 220px; border-radius: 50%; background: #2F63D8; opacity: 0.35; filter: blur(60px)"></span>
<span style="position: absolute; right: -60px; top: -80px; width: 220px; height: 220px; border-radius: 50%; background: #E0424B; opacity: 0.35; filter: blur(60px)"></span>
<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 12px 4px">
<a href="Partido.dc.html" aria-label="Back to match" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>
<div style="flex-grow: 1; display: flex; align-items: center; justify-content: center; gap: 12px">
<span style="width: 32px; height: 32px; border-radius: 50%; background: #2F63D8; font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center">RIV</span>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 30px; letter-spacing: 1px">2 – 1</span>
<span style="width: 32px; height: 32px; border-radius: 50%; background: #E0424B; font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center">ASH</span>
</div>
<span style="width: 44px; display: flex; justify-content: center"><span style="padding: 3px 9px; border-radius: 11px; background: #C8FF3D; color: #0A0C11; font-size: 12px; font-weight: 800">67'</span></span>
</header>
</div>

@@TABS@@

<div style="display: flex; gap: 8px; padding: 0 16px">
<sc-for list="{{periodos}}" as="p" hint-placeholder-count="3">
<button style="height: 38px; padding: 0 18px; border-radius: 19px; border: 1px solid {{p.borde}}; background: {{p.fondo}}; color: #FFFFFF; font-size: 13px; font-weight: 700">{{p.nombre}}</button>
</sc-for>
</div>

<section style="margin: 0 12px; padding: 18px 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; align-items: center; gap: 16px">
<svg width="132" height="132" viewBox="0 0 132 132" role="img" aria-label="Possession: Riverton 58 percent, Ashford 42 percent" style="flex-shrink: 0">
<circle cx="66" cy="66" r="52" fill="none" stroke="#E0424B" stroke-width="14"></circle>
<circle cx="66" cy="66" r="52" fill="none" stroke="#2F63D8" stroke-width="14" stroke-dasharray="189.5 326.7" stroke-linecap="butt" transform="rotate(-90 66 66)"></circle>
<text x="66" y="64" text-anchor="middle" fill="#F1F3F8" font-family="Archivo, sans-serif" font-weight="800" font-size="30">58%</text>
<text x="66" y="82" text-anchor="middle" fill="#8E96AA" font-family="Instrument Sans, sans-serif" font-size="11">possession</text>
</svg>
<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 12px; height: 12px; border-radius: 4px; background: #2F63D8"></span><div style="display: flex; flex-direction: column"><span style="font-size: 12px; color: #8E96AA">Riverton</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 22px">58%</span></div></div>
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 12px; height: 12px; border-radius: 4px; background: #E0424B"></span><div style="display: flex; flex-direction: column"><span style="font-size: 12px; color: #8E96AA">Ashford Utd</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 22px">42%</span></div></div>
<span style="font-size: 12px; color: #C6CBD8">Riverton have had the ball 16 points more than their average.</span>
</div>
</section>

<sc-for list="{{bloques}}" as="b" hint-placeholder-count="4">
<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 8px; height: 22px; border-radius: 4px; background: #C8FF3D"></span><span style="font-size: 16px; font-weight: 700">{{b.titulo}}</span></div>
<sc-for list="{{b.filas}}" as="s" hint-placeholder-count="5">
<div style="display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 18px; width: 70px">{{s.h}}</span><span style="font-size: 12px; font-weight: 600; color: #8E96AA">{{s.nombre}}</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 18px; width: 70px; text-align: right">{{s.a}}</span></div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px"><div style="height: 7px; border-radius: 4px 0 0 4px; background: #1E2330; display: flex; justify-content: flex-end"><span style="width: {{s.wh}}%; height: 7px; border-radius: 4px 0 0 4px; background: #2F63D8"></span></div><div style="height: 7px; border-radius: 0 4px 4px 0; background: #1E2330"><span style="display: block; width: {{s.wa}}%; height: 7px; border-radius: 0 4px 4px 0; background: #E0424B"></span></div></div>
</div>
</sc-for>
</section>
</sc-for>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    const periodos = ['All', '1st half', '2nd half'].map((nombre, i) => ({ nombre, fondo: i === 0 ? '#4A63FF' : '#12151C', borde: i === 0 ? '#4A63FF' : '#262C3B' }));
    const S = (nombre, h, a, dec, pct) => {
      const t = h + a;
      const f = (v) => (dec ? v.toFixed(1) : String(v)) + (pct ? '%' : '');
      return { nombre, h: f(h), a: f(a), wh: Math.round(h / t * 100), wa: Math.round(a / t * 100) };
    };
    const bloques = [
      { titulo: 'Shots', filas: [S('Expected goals (xG)', 1.9, 0.8, true), S('Total shots', 12, 6), S('On target', 6, 2), S('Big chances', 3, 1), S('Shots inside box', 9, 3)] },
      { titulo: 'Passing', filas: [S('Passes', 412, 301), S('Accuracy', 88, 81, false, true), S('Key passes', 8, 3), S('Into final third', 46, 22), S('Crosses', 14, 9)] },
      { titulo: 'Defending', filas: [S('Tackles won', 9, 12), S('Interceptions', 7, 11), S('Clearances', 8, 21), S('Saves', 1, 4), S('Duels won', 48, 52, false, true)] },
      { titulo: 'Discipline', filas: [S('Fouls', 9, 13), S('Yellow cards', 1, 3), S('Red cards', 0, 1), S('Offsides', 2, 4)] }
    ];
    // Red cards 0 vs 1 would divide by zero shares: keep the bar honest.
    bloques[3].filas[2] = { nombre: 'Red cards', h: '0', a: '1', wh: 0, wa: 100 };
    return { periodos, bloques };
  }
}'''
page("Stats.dc.html", "Match stats", 390, 2140, BODY, JS, nav_active="m", tabs_active="Stats")

# ---------------------------------------------------------------- LINEUPS
BODY = r'''
<div style="position: relative; width: 390px; height: 1620px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: -60px; top: -80px; width: 220px; height: 220px; border-radius: 50%; background: #2F63D8; opacity: 0.35; filter: blur(60px)"></span>
<span style="position: absolute; right: -60px; top: -80px; width: 220px; height: 220px; border-radius: 50%; background: #E0424B; opacity: 0.35; filter: blur(60px)"></span>
<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 12px 4px">
<a href="Partido.dc.html" aria-label="Back to match" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>
<div style="flex-grow: 1; display: flex; align-items: center; justify-content: center; gap: 12px">
<span style="width: 32px; height: 32px; border-radius: 50%; background: #2F63D8; font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center">RIV</span>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 30px; letter-spacing: 1px">2 – 1</span>
<span style="width: 32px; height: 32px; border-radius: 50%; background: #E0424B; font-size: 10px; font-weight: 800; display: flex; align-items: center; justify-content: center">ASH</span>
</div>
<span style="width: 44px; display: flex; justify-content: center"><span style="padding: 3px 9px; border-radius: 11px; background: #C8FF3D; color: #0A0C11; font-size: 12px; font-weight: 800">67'</span></span>
</header>
</div>

@@TABS@@

<div style="display: flex; justify-content: space-between; align-items: center; padding: 0 16px">
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 12px; height: 12px; border-radius: 50%; background: #2F63D8"></span><span style="font-size: 14px; font-weight: 700">Riverton</span><span style="padding: 2px 8px; border-radius: 8px; background: #1A1E28; font-size: 12px; font-weight: 700; color: #C6CBD8">4-3-3</span></div>
<div style="display: flex; align-items: center; gap: 8px"><span style="padding: 2px 8px; border-radius: 8px; background: #1A1E28; font-size: 12px; font-weight: 700; color: #C6CBD8">4-4-2</span><span style="font-size: 14px; font-weight: 700">Ashford Utd</span><span style="width: 12px; height: 12px; border-radius: 50%; background: #E0424B"></span></div>
</div>

<section style="margin: 0 12px; position: relative; height: 660px; border-radius: 26px; background: #0F1B15; border: 1px solid #1F3026; overflow: hidden" aria-label="Pitch with both starting elevens">
<div style="position: absolute; left: 14px; right: 14px; top: 14px; bottom: 14px; border: 2px solid #25392E; border-radius: 6px"></div>
<div style="position: absolute; left: 14px; right: 14px; top: 329px; height: 2px; background: #25392E"></div>
<div style="position: absolute; left: 50%; top: 330px; width: 88px; height: 88px; margin: -44px 0 0 -44px; border: 2px solid #25392E; border-radius: 50%"></div>
<div style="position: absolute; left: 50%; top: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-top: none"></div>
<div style="position: absolute; left: 50%; bottom: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-bottom: none"></div>
<sc-for list="{{jugadores}}" as="j" hint-placeholder-count="22">
<div style="position: absolute; left: {{j.x}}%; top: {{j.y}}%; width: 68px; margin-left: -34px; margin-top: -24px; display: flex; flex-direction: column; align-items: center; gap: 3px">
<div style="position: relative; width: 36px; height: 36px">
<span style="width: 36px; height: 36px; border-radius: 50%; background: {{j.bg}}; color: #FFFFFF; font-size: 13px; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 2px rgba(255,255,255,0.85)">{{j.num}}</span>
<span style="position: absolute; right: -14px; top: -8px; padding: 1px 6px; border-radius: 8px; background: {{j.rbg}}; color: {{j.rfg}}; font-size: 10px; font-weight: 800">{{j.rating}}</span>
</div>
<span style="font-size: 11px; font-weight: 700; text-align: center; white-space: nowrap; text-shadow: 0 1px 2px #000">{{j.nombre}}</span>
</div>
</sc-for>
</section>

<div style="display: flex; gap: 14px; padding: 0 16px; font-size: 11px; color: #8E96AA; align-items: center">
<span style="font-weight: 700; color: #F1F3F8">Rating</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: #C8FF3D; color: #0A0C11; font-weight: 800">7.5+</span>strong</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: #3A4256; color: #FFFFFF; font-weight: 800">6.5</span>fine</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: #FF8A3D; color: #0A0C11; font-weight: 800">&lt;6.5</span>weak</span>
</div>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<span style="font-size: 16px; font-weight: 700">Bench</span>
<sc-for list="{{banquillo}}" as="b" hint-placeholder-count="4">
<div style="display: flex; align-items: center; gap: 10px">
<span style="width: 30px; height: 30px; border-radius: 50%; background: {{b.bg}}; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{b.num}}</span>
<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{{b.nombre}}</span>
<span style="font-size: 12px; color: #8E96AA">{{b.nota}}</span>
</div>
</sc-for>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<span style="font-size: 16px; font-weight: 700">Not playing</span>
<sc-for list="{{fuera}}" as="f" hint-placeholder-count="3">
<div style="display: flex; align-items: center; gap: 10px">
<span style="width: 30px; height: 30px; border-radius: 50%; background: {{f.bg}}; font-size: 9px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{f.club}}</span>
<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{{f.nombre}}</span>
<span style="padding: 3px 10px; border-radius: 10px; background: {{f.tagBg}}; color: {{f.tagFg}}; font-size: 12px; font-weight: 700">{{f.tag}}</span>
</div>
</sc-for>
</section>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    // Sample data. Invented players and clubs.
    const rc = (r) => r >= 7.5 ? ['#C8FF3D', '#0A0C11'] : r >= 6.5 ? ['#3A4256', '#FFFFFF'] : ['#FF8A3D', '#0A0C11'];
    const fila = (eq, y, nombres, nums, ratings) => nombres.map((nombre, i) => {
      const n = nombres.length, x = n === 1 ? 50 : 13 + i * (74 / (n - 1));
      const [rbg, rfg] = rc(ratings[i]);
      return { x: Math.round(x * 10) / 10, y, nombre, num: nums[i], rating: ratings[i].toFixed(1), rbg, rfg, bg: eq === 'h' ? '#2F63D8' : '#E0424B' };
    });
    const jugadores = [
      ...fila('h', 8, ['Brandt'], [1], [6.9]),
      ...fila('h', 19, ['Osei', 'Vance', 'Roca', 'Hale'], [2, 4, 5, 3], [7.1, 6.8, 7.4, 6.6]),
      ...fila('h', 31, ['Moreau', 'Keane', 'Lindqvist'], [8, 6, 10], [7.0, 7.3, 8.2]),
      ...fila('h', 43, ['Tanaka', 'Okafor', 'Diaz'], [11, 9, 7], [6.4, 8.6, 7.7]),
      ...fila('a', 57, ['Marsh', 'Rossi'], [9, 10], [7.6, 6.1]),
      ...fila('a', 69, ['Pike', 'Novak', 'Duarte', 'Sato'], [7, 8, 6, 11], [6.3, 6.6, 6.8, 6.2]),
      ...fila('a', 81, ['Ward', 'Haas', 'Ilic', 'Cruz'], [2, 4, 5, 3], [6.9, 6.7, 6.5, 6.4]),
      ...fila('a', 93, ['Ferro'], [1], [7.2])
    ];
    const banquillo = [
      { num: 14, nombre: 'Sorensen', nota: 'Riverton · midfield', bg: '#2F63D8' },
      { num: 19, nombre: 'Baptiste', nota: 'Riverton · forward', bg: '#2F63D8' },
      { num: 15, nombre: 'Kovac', nota: 'Ashford · defender', bg: '#E0424B' },
      { num: 20, nombre: 'Yilmaz', nota: 'Ashford · forward', bg: '#E0424B' }
    ];
    const fuera = [
      { club: 'RIV', bg: '#2F63D8', nombre: 'D. Kessler', tag: 'Injured', tagBg: '#3A2412', tagFg: '#FFB27A' },
      { club: 'ASH', bg: '#E0424B', nombre: 'T. Bergman', tag: 'Suspended', tagBg: '#3A2412', tagFg: '#FFB27A' },
      { club: 'ASH', bg: '#E0424B', nombre: 'L. Amara', tag: 'Doubtful', tagBg: '#1E2330', tagFg: '#C6CBD8' }
    ];
    return { jugadores, banquillo, fuera };
  }
}'''
page("Alineacion.dc.html", "Lineups", 390, 1620, BODY, JS, nav_active="m", tabs_active="Lineups")
print("s2 ok")
