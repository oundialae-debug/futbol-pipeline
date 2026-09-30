from common import *

# ---------------------------------------------------------------- MAIN
BODY = r'''
<div style="position: relative; width: 390px; height: 1700px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px">
<a href="Main.dc.html" aria-label="2yellow home" style="flex-grow: 1; display: flex; align-items: center; gap: 6px"><svg width="38" height="38" viewBox="0 0 48 48" aria-hidden="true"><defs><clipPath id="cAhdr"><rect x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)"></rect></clipPath></defs><rect x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)" fill="#FFD21F"></rect><rect x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)" fill="#FFD21F" stroke="#0A0C11" stroke-width="2"></rect><rect x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)" fill="#FF3B3B" stroke="#0A0C11" stroke-width="2" clip-path="url(#cAhdr)"></rect></svg><span style="font-family: 'Archivo', sans-serif; font-stretch: 78%; font-weight: 900; font-size: 27px; line-height: 1; letter-spacing: -0.5px; color: #F1F3F8"><span style="color: #FFD21F">2</span>yellow</span></a>
<button aria-label="Search" style="width: 44px; height: 44px; border: none; border-radius: 22px; background: #161A23; color: #F1F3F8; display: flex; align-items: center; justify-content: center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg></button>
<button aria-label="Profile" style="width: 44px; height: 44px; border: 2px solid #4A63FF; border-radius: 22px; background: #1A1E28; color: #F1F3F8; font-weight: 800; font-size: 15px">A</button>
</header>

<div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px 0 16px">
<span style="display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700"><span style="width: 9px; height: 9px; border-radius: 50%; background: #C8FF3D"></span>Live now</span>
<a href="#" style="font-size: 13px; font-weight: 600; color: #8FA2FF">See all 6</a>
</div>

<div style="display: flex; gap: 12px; padding: 0 16px; overflow: hidden">
<sc-for list="{{vivos}}" as="c" hint-placeholder-count="2">
<a href="{{c.enlace}}" style="position: relative; flex-shrink: 0; width: 304px; height: 188px; box-sizing: border-box; border-radius: 26px; background: #12151C; border: 1px solid #262C3B; overflow: hidden; display: block">
<span style="position: absolute; left: -40px; top: -50px; width: 170px; height: 170px; border-radius: 50%; background: {{c.cl}}; opacity: 0.42; filter: blur(46px)"></span>
<span style="position: absolute; right: -40px; top: -50px; width: 170px; height: 170px; border-radius: 50%; background: {{c.cv}}; opacity: 0.42; filter: blur(46px)"></span>
<div style="position: relative; display: flex; flex-direction: column; gap: 12px; padding: 14px 16px">
<div style="display: flex; justify-content: space-between; align-items: center">
<span style="font-size: 12px; font-weight: 600; color: #C6CBD8">{{c.liga}}</span>
<span style="display: flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 12px; background: #C8FF3D; color: #0A0C11; font-size: 12px; font-weight: 800"><span style="width: 6px; height: 6px; border-radius: 50%; background: #0A0C11"></span>{{c.min}}</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="width: 86px; display: flex; flex-direction: column; align-items: center; gap: 6px"><span style="width: 46px; height: 46px; border-radius: 50%; background: {{c.cl}}; color: {{c.tl}}; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 2px rgba(255,255,255,0.18)">{{c.il}}</span><span style="font-size: 12px; font-weight: 600">{{c.local}}</span></div>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 46px; line-height: 1; letter-spacing: 1px">{{c.gl}} – {{c.gv}}</span>
<div style="width: 86px; display: flex; flex-direction: column; align-items: center; gap: 6px"><span style="width: 46px; height: 46px; border-radius: 50%; background: {{c.cv}}; color: {{c.tv}}; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 2px rgba(255,255,255,0.18)">{{c.iv}}</span><span style="font-size: 12px; font-weight: 600">{{c.visitante}}</span></div>
</div>
<div style="display: flex; align-items: center; gap: 8px">
<span style="font-size: 11px; font-weight: 700; color: #C6CBD8; width: 46px">xG {{c.xh}}</span>
<div style="flex-grow: 1; display: flex; height: 5px; border-radius: 3px; overflow: hidden; gap: 2px"><span style="width: {{c.a}}%; background: {{c.cl}}"></span><span style="width: {{c.b}}%; background: #3A4256"></span><span style="width: {{c.c}}%; background: {{c.cv}}"></span></div>
<span style="font-size: 11px; font-weight: 700; color: #C6CBD8; width: 46px; text-align: right">{{c.xa}} xG</span>
</div>
</div>
</a>
</sc-for>
</div>

<nav aria-label="Days" style="display: flex; gap: 6px; padding: 4px 16px 0 16px">
<sc-for list="{{dias}}" as="d" hint-placeholder-count="7">
<button aria-current="{{d.actual}}" style="flex: 1 1 0; min-width: 0; height: 60px; border-radius: 18px; border: 1px solid {{d.borde}}; background: {{d.fondo}}; color: {{d.texto}}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px">
<span style="font-size: 10px; font-weight: 700; letter-spacing: 0.6px; opacity: 0.8">{{d.dow}}</span>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 21px; line-height: 1">{{d.num}}</span>
</button>
</sc-for>
</nav>

<div style="display: flex; gap: 8px; padding: 0 16px">
<sc-for list="{{filtros}}" as="f" hint-placeholder-count="4">
<button style="height: 38px; padding: 0 16px; border-radius: 19px; border: 1px solid {{f.borde}}; background: {{f.fondo}}; color: {{f.texto}}; font-size: 13px; font-weight: 700; white-space: nowrap">{{f.nombre}}</button>
</sc-for>
</div>

<sc-for list="{{ligas}}" as="l" hint-placeholder-count="2">
<section style="margin: 0 12px; border-radius: 24px; background: #12151C; border: 1px solid #232838; overflow: hidden">
<div style="display: flex; align-items: center; gap: 10px; padding: 14px 14px 12px 14px">
<span style="width: 30px; height: 30px; border-radius: 10px; background: {{l.color}}; color: #FFFFFF; font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 12px; display: flex; align-items: center; justify-content: center">{{l.sigla}}</span>
<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 15px; font-weight: 700">{{l.nombre}}</span><span style="font-size: 12px; color: #8E96AA">{{l.ronda}}</span></div>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8E96AA" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>
</div>
<sc-for list="{{l.partidos}}" as="p" hint-placeholder-count="3">
<a href="{{p.enlace}}" style="display: flex; flex-direction: column; gap: 10px; padding: 13px 14px 13px 14px; border-top: 1px solid #1E2330">
<div style="display: flex; align-items: center; gap: 12px">
<div style="width: 46px; display: flex; flex-direction: column; align-items: center; gap: 3px"><span style="font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 15px; color: {{p.tColor}}">{{p.tiempo}}</span></div>
<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 7px">
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 22px; height: 22px; flex-shrink: 0; border-radius: 50%; background: {{p.cl}}; color: {{p.tl}}; font-size: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{p.il}}</span><span style="font-size: 15px; font-weight: {{p.wl}}">{{p.local}}</span></div>
<div style="display: flex; align-items: center; gap: 8px"><span style="width: 22px; height: 22px; flex-shrink: 0; border-radius: 50%; background: {{p.cv}}; color: {{p.tv}}; font-size: 8px; font-weight: 800; display: flex; align-items: center; justify-content: center">{{p.iv}}</span><span style="font-size: 15px; font-weight: {{p.wv}}">{{p.visitante}}</span></div>
</div>
<div style="width: 26px; display: flex; flex-direction: column; align-items: center; gap: 7px"><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px; line-height: 22px">{{p.gl}}</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px; line-height: 22px">{{p.gv}}</span></div>
</div>
<div style="margin-left: 58px; display: flex; align-items: center; gap: 8px">
<div style="width: 90px; display: flex; height: 6px; border-radius: 3px; overflow: hidden; gap: 2px" aria-hidden="true"><span style="width: {{p.a}}%; background: {{p.cl}}"></span><span style="width: {{p.b}}%; background: #3A4256"></span><span style="width: {{p.c}}%; background: {{p.cv}}"></span></div>
<span style="font-size: 11px; font-weight: 600; color: #8E96AA; white-space: nowrap">{{p.a}} · {{p.b}} · {{p.c}}</span>
<span style="margin-left: auto; padding: 3px 9px; border-radius: 9px; background: {{p.chipFondo}}; color: {{p.chipTexto}}; font-size: 11px; font-weight: 700; white-space: nowrap">{{p.chip}}</span>
</div>
</a>
</sc-for>
</section>
</sc-for>

<div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px 0 16px">
<span style="font-size: 18px; font-weight: 700">Top tips today</span>
<a href="Tips.dc.html" style="font-size: 13px; font-weight: 600; color: #8FA2FF">All tips</a>
</div>
<div style="display: flex; gap: 10px; padding: 0 16px; overflow: hidden">
<sc-for list="{{tips}}" as="t" hint-placeholder-count="3">
<a href="Tips.dc.html" style="flex-shrink: 0; width: 176px; box-sizing: border-box; padding: 14px; border-radius: 22px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 6px">
<span style="font-size: 12px; font-weight: 600; color: #8E96AA">{{t.partido}}</span>
<span style="font-size: 15px; font-weight: 700">{{t.mercado}}</span>
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 40px; line-height: 1; color: #C8FF3D">{{t.pct}}<span style="font-size: 22px">%</span></span>
<span style="align-self: flex-start; padding: 3px 9px; border-radius: 9px; background: #1E2330; color: #C6CBD8; font-size: 11px; font-weight: 700">Books hit {{t.casa}}%</span>
</a>
</sc-for>
</div>

@@NAV@@
</div>
'''

JS = r'''class Component extends DCLogic {
  renderVals() {
    const dias = [['MON', 14], ['TUE', 15], ['WED', 16], ['THU', 17], ['FRI', 18], ['SAT', 19], ['SUN', 20]].map(([dow, num], i) => {
      const on = i === 2;
      return { dow, num, actual: on ? 'date' : 'false', fondo: on ? '#F1F3F8' : '#12151C', texto: on ? '#0A0C11' : '#F1F3F8', borde: on ? '#F1F3F8' : '#232838' };
    });
    const filtros = ['All', 'Following', 'Tips', 'Big games'].map((nombre, i) => ({ nombre, fondo: i === 0 ? '#4A63FF' : '#12151C', texto: '#FFFFFF', borde: i === 0 ? '#4A63FF' : '#262C3B' }));
    // Sample data. Invented clubs.
    const E = { RIV: ['#2F63D8', '#FFFFFF'], ASH: ['#E0424B', '#FFFFFF'], CAL: ['#E8ECF3', '#0A0C11'], BAY: ['#F2C230', '#0A0C11'], NOR: ['#2FA36B', '#FFFFFF'], HAR: ['#9B4FD0', '#FFFFFF'], VAL: ['#E8ECF3', '#0A0C11'], OAK: ['#F07A2A', '#0A0C11'], LAK: ['#33B5E5', '#0A0C11'], STO: ['#7C8496', '#FFFFFF'] };
    const V = (liga, min, il, local, gl, iv, visitante, gv, xh, xa, a, b, c, enlace) => ({
      liga, min, il, local, gl, iv, visitante, gv, xh, xa, a, b, c, enlace: enlace || '#',
      cl: E[il][0], tl: E[il][1], cv: E[iv][0], tv: E[iv][1]
    });
    const vivos = [
      V('Coastal League', "67'", 'RIV', 'Riverton', 2, 'ASH', 'Ashford Utd', 1, '1.9', '0.8', 62, 22, 16, 'Partido.dc.html'),
      V('Metro Cup', "31'", 'LAK', 'Lakeside', 0, 'VAL', 'Vale Rovers', 0, '0.7', '0.9', 33, 31, 36)
    ];
    const chip = { xg: ['#1E2A66', '#A9B8FF'], tip: ['#26301A', '#C8FF3D'], tight: ['#3A2412', '#FFB27A'] };
    const P = (tiempo, estado, il, local, iv, visitante, gl, gv, a, b, c, ch, tipo) => {
      const ganaL = gl !== '' && gl > gv, ganaV = gl !== '' && gv > gl;
      return { tiempo, il, local, iv, visitante, gl, gv, a, b, c, chip: ch, enlace: '#',
        tColor: estado === 'ft' ? '#8E96AA' : '#F1F3F8',
        cl: E[il][0], tl: E[il][1], cv: E[iv][0], tv: E[iv][1],
        wl: ganaL ? 700 : 500, wv: ganaV ? 700 : 500, chipFondo: chip[tipo][0], chipTexto: chip[tipo][1] };
    };
    const ligas = [
      { sigla: 'CL', nombre: 'Coastal League', ronda: 'Matchday 12', color: '#4A63FF', partidos: [
        P('18:30', 'next', 'CAL', 'Calder City', 'BAY', 'Bayfield', '', '', 48, 27, 25, 'Over 2.5 · 61%', 'tip'),
        P('20:45', 'next', 'NOR', 'Northgate', 'HAR', 'Harbor Town', '', '', 41, 29, 30, 'Tight game', 'tight'),
        P('FT', 'ft', 'OAK', 'Oakmont', 'STO', 'Stonebridge', 0, 3, 39, 30, 31, 'xG 0.6 – 2.4', 'xg')
      ] },
      { sigla: 'MC', nombre: 'Metro Cup', ronda: 'Round of 16', color: '#7A4FE0', partidos: [
        P('21:00', 'next', 'VAL', 'Vale Rovers', 'LAK', 'Lakeside', '', '', 34, 31, 35, 'Tight game', 'tight'),
        P('FT', 'ft', 'LAK', 'Lakeside', 'VAL', 'Vale Rovers', 1, 1, 44, 28, 28, 'xG 1.3 – 1.5', 'xg')
      ] }
    ];
    const tips = [
      { partido: 'Riverton – Ashford', mercado: 'Over 1.5 goals', pct: 88, casa: 78 },
      { partido: 'Calder – Bayfield', mercado: 'Both teams score', pct: 64, casa: 59 },
      { partido: 'Northgate – Harbor', mercado: 'Under 3.5 goals', pct: 79, casa: 62 }
    ];
    return { dias, filtros, vivos, ligas, tips };
  }
}'''
page("Main.dc.html", "Matches", 390, 1700, BODY, JS, nav_active="m")

# ---------------------------------------------------------------- MATCH
BODY = r'''
<div style="position: relative; width: 390px; height: 2260px; box-sizing: border-box; background: #0A0C11; overflow: hidden; display: flex; flex-direction: column; gap: 14px">

<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: -60px; top: -60px; width: 240px; height: 240px; border-radius: 50%; background: #2F63D8; opacity: 0.4; filter: blur(60px)"></span>
<span style="position: absolute; right: -60px; top: -60px; width: 240px; height: 240px; border-radius: 50%; background: #E0424B; opacity: 0.4; filter: blur(60px)"></span>
<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 0 4px">
<a href="Main.dc.html" aria-label="Back to matches" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>
<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 700">Coastal League</span><span style="font-size: 12px; color: #C6CBD8">Matchday 12 · Wed 16 Sep</span></div>
<button aria-label="Follow match" style="width: 44px; height: 44px; border: none; background: transparent; color: #F1F3F8"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.4 5.6 6.1.5-4.6 4 1.4 6-5.3-3.2-5.3 3.2 1.4-6-4.6-4 6.1-.5z"></path></svg></button>
<button aria-label="Share" style="width: 44px; height: 44px; border: none; background: transparent; color: #F1F3F8"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V4M8 8l4-4 4 4M5 13v6h14v-6"></path></svg></button>
</header>
<div style="position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 0 16px">
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center"><span style="width: 62px; height: 62px; border-radius: 50%; background: #2F63D8; color: #FFFFFF; font-weight: 800; font-size: 16px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 3px rgba(255,255,255,0.2)">RIV</span><span style="font-size: 15px; font-weight: 700">Riverton</span><span style="font-size: 12px; color: #C6CBD8">3rd · W W D W L</span></div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; padding-top: 4px">
<span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 64px; line-height: 1; letter-spacing: 1px">2 – 1</span>
<span style="display: flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 13px; background: #C8FF3D; color: #0A0C11; font-size: 14px; font-weight: 800"><span style="width: 7px; height: 7px; border-radius: 50%; background: #0A0C11"></span>67'</span>
</div>
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center"><span style="width: 62px; height: 62px; border-radius: 50%; background: #E0424B; color: #FFFFFF; font-weight: 800; font-size: 16px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 3px rgba(255,255,255,0.2)">ASH</span><span style="font-size: 15px; font-weight: 700">Ashford Utd</span><span style="font-size: 12px; color: #C6CBD8">7th · L W W D L</span></div>
</div>
<div style="position: relative; display: flex; justify-content: space-between; padding: 12px 16px 0 16px; font-size: 12px; line-height: 1.5; color: #C6CBD8"><span style="width: 150px">Okafor 12'<br>Lindqvist 58'</span><span style="width: 150px; text-align: right">Marsh 34'</span></div>
<div style="position: relative; padding: 14px 16px 16px 16px; display: flex; flex-direction: column; gap: 6px">
<div style="position: relative; height: 24px" aria-label="Match timeline">
<div style="position: absolute; left: 0; right: 0; top: 11px; height: 2px; background: #3A4256"></div>
<div style="position: absolute; left: 0; width: 74%; top: 11px; height: 2px; background: #C8FF3D"></div>
<span style="position: absolute; left: 13%; top: 3px; width: 18px; height: 18px; margin-left: -9px; border-radius: 50%; background: #2F63D8; box-shadow: 0 0 0 2px #0A0C11"></span>
<span style="position: absolute; left: 37.7%; top: 3px; width: 18px; height: 18px; margin-left: -9px; border-radius: 50%; background: #E0424B; box-shadow: 0 0 0 2px #0A0C11"></span>
<span style="position: absolute; left: 45.5%; top: 6px; width: 10px; height: 14px; margin-left: -5px; border-radius: 2px; background: #FFD24A"></span>
<span style="position: absolute; left: 64.4%; top: 3px; width: 18px; height: 18px; margin-left: -9px; border-radius: 50%; background: #2F63D8; box-shadow: 0 0 0 2px #0A0C11"></span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 10px; color: #8E96AA"><span>0'</span><span>HT</span><span>90'</span></div>
</div>
</div>

@@TABS@@

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Win chance</span><span style="font-size: 12px; color: #8E96AA">updated 67'</span></div>
<div style="display: flex; height: 48px; border-radius: 14px; overflow: hidden; gap: 3px">
<div style="width: 62%; background: #2F63D8; display: flex; align-items: center; justify-content: space-between; padding: 0 14px"><span style="font-size: 12px; font-weight: 700">Riverton</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 26px">62</span></div>
<div style="width: 22%; background: #3A4256; display: flex; align-items: center; justify-content: center; font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 20px">22</div>
<div style="width: 16%; background: #E0424B; display: flex; align-items: center; justify-content: center; font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800; font-size: 20px">16</div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: #1A1E28"><span style="display: block; font-size: 11px; color: #8E96AA">Fair odds · 1</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">1.61</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: #1A1E28"><span style="display: block; font-size: 11px; color: #8E96AA">Fair odds · X</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">4.55</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: #1A1E28"><span style="display: block; font-size: 11px; color: #8E96AA">Fair odds · 2</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 80%; font-weight: 800; font-size: 20px">6.25</span></div>
</div>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">xG race</span><span style="font-size: 12px; color: #8E96AA">expected goals as the match goes</span></div>
<svg width="342" height="132" viewBox="0 0 342 132" role="img" aria-label="Cumulative expected goals: Riverton 1.9, Ashford 0.8 at 67 minutes" style="display: block; max-width: 100%">
<line x1="0" y1="100" x2="342" y2="100" stroke="#2A3040" stroke-width="1"></line>
<line x1="171" y1="4" x2="171" y2="100" stroke="#2A3040" stroke-width="1" stroke-dasharray="3 4"></line>
<line x1="254.6" y1="4" x2="254.6" y2="100" stroke="#C8FF3D" stroke-width="1" stroke-dasharray="2 3"></line>
<polyline points="0,100 45.6,87.7 76,77.5 129.2,67.3 155.8,59.1 190,46.8 220.4,28.4 254.6,22.3" fill="none" stroke="#2F63D8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
<polyline points="0,100 45.6,95.9 76,91.8 129.2,79.5 155.8,77.5 190,75.5 220.4,71.4 254.6,67.3" fill="none" stroke="#E0424B" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
<circle cx="45.6" cy="87.7" r="5.5" fill="#0A0C11" stroke="#2F63D8" stroke-width="3"></circle>
<circle cx="220.4" cy="28.4" r="5.5" fill="#0A0C11" stroke="#2F63D8" stroke-width="3"></circle>
<circle cx="129.2" cy="79.5" r="5.5" fill="#0A0C11" stroke="#E0424B" stroke-width="3"></circle>
<text x="262" y="26" fill="#8FA2FF" font-size="12" font-weight="700" font-family="Instrument Sans, sans-serif">1.9</text>
<text x="262" y="71" fill="#FF8C92" font-size="12" font-weight="700" font-family="Instrument Sans, sans-serif">0.8</text>
<text x="0" y="122" fill="#8E96AA" font-size="10" font-family="Instrument Sans, sans-serif">0'</text>
<text x="160" y="122" fill="#8E96AA" font-size="10" font-family="Instrument Sans, sans-serif">HT</text>
<text x="318" y="122" fill="#8E96AA" font-size="10" font-family="Instrument Sans, sans-serif">90'</text>
</svg>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Shot map</span><span style="font-size: 12px; color: #8E96AA">bigger dot = better chance</span></div>
<svg width="342" height="230" viewBox="0 0 342 230" role="img" aria-label="Shot map: Riverton 12 shots, Ashford 6 shots" style="display: block; max-width: 100%; border-radius: 16px; background: #0F1B15">
<rect x="6" y="6" width="330" height="218" rx="4" fill="none" stroke="#25392E" stroke-width="2"></rect>
<rect x="96" y="6" width="150" height="76" fill="none" stroke="#25392E" stroke-width="2"></rect>
<rect x="136" y="6" width="70" height="28" fill="none" stroke="#25392E" stroke-width="2"></rect>
<path d="M136 82 A 36 36 0 0 0 206 82" fill="none" stroke="#25392E" stroke-width="2"></path>
<circle cx="171" cy="60" r="2.5" fill="#25392E"></circle>
<path d="M136 224 A 36 36 0 0 1 206 224" fill="none" stroke="#25392E" stroke-width="2"></path>
<circle cx="171" cy="30" r="9" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="150" cy="52" r="13" fill="#2F63D8" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="188" cy="46" r="8" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="120" cy="70" r="6" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="214" cy="74" r="5" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="171" cy="104" r="5" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="140" cy="118" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="200" cy="130" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="90" cy="108" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="250" cy="120" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="171" cy="150" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="112" cy="150" r="4" fill="#2F63D8" fill-opacity="0.85"></circle>
<circle cx="160" cy="44" r="11" fill="#E0424B" fill-opacity="0.85" stroke="#C8FF3D" stroke-width="3"></circle>
<circle cx="196" cy="88" r="7" fill="#E0424B" fill-opacity="0.85"></circle>
<circle cx="132" cy="96" r="5" fill="#E0424B" fill-opacity="0.85"></circle>
<circle cx="230" cy="112" r="4" fill="#E0424B" fill-opacity="0.85"></circle>
<circle cx="110" cy="134" r="4" fill="#E0424B" fill-opacity="0.85"></circle>
<circle cx="180" cy="168" r="4" fill="#E0424B" fill-opacity="0.85"></circle>
</svg>
<div style="display: flex; gap: 16px; font-size: 12px; color: #C6CBD8; align-items: center">
<span style="display: flex; align-items: center; gap: 6px"><span style="width: 10px; height: 10px; border-radius: 50%; background: #2F63D8"></span>Riverton 12</span>
<span style="display: flex; align-items: center; gap: 6px"><span style="width: 10px; height: 10px; border-radius: 50%; background: #E0424B"></span>Ashford 6</span>
<span style="display: flex; align-items: center; gap: 6px; margin-left: auto"><span style="width: 10px; height: 10px; border-radius: 50%; border: 2px solid #C8FF3D; box-sizing: border-box"></span>Goal</span>
</div>
</section>

<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 14px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px: font-weight: 700; font-weight: 700">Key stats</span><a href="Stats.dc.html" style="font-size: 13px; font-weight: 600; color: #8FA2FF">All stats</a></div>
<sc-for list="{{stats}}" as="s" hint-placeholder-count="5">
<div style="display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 18px; width: 64px">{{s.h}}</span><span style="font-size: 12px; font-weight: 600; color: #8E96AA">{{s.nombre}}</span><span style="font-family: 'Archivo', sans-serif; font-stretch: 85%; font-weight: 800; font-size: 18px; width: 64px; text-align: right">{{s.a}}</span></div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px"><div style="height: 7px; border-radius: 4px 0 0 4px; background: #1E2330; display: flex; justify-content: flex-end"><span style="width: {{s.wh}}%; height: 7px; border-radius: 4px 0 0 4px; background: #2F63D8"></span></div><div style="height: 7px; border-radius: 0 4px 4px 0; background: #1E2330"><span style="display: block; width: {{s.wa}}%; height: 7px; border-radius: 0 4px 4px 0; background: #E0424B"></span></div></div>
</div>
</sc-for>
</section>

<section style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: #12151C; border: 1px solid #232838; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; align-items: center; gap: 12px"><span style="width: 40px; height: 40px; border-radius: 50%; background: #1A1E28; display: flex; align-items: center; justify-content: center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F1F3F8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="3" width="10" height="15" rx="2" transform="rotate(12 11 10)"></rect></svg></span><div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 700">M. Alder</span><span style="font-size: 12px; color: #8E96AA">Referee · 5.3 cards per match</span></div><span style="padding: 3px 10px; border-radius: 10px; background: #3A2412; color: #FFB27A; font-size: 12px; font-weight: 700">Strict</span></div>
<div style="display: flex; gap: 8px"><span style="flex: 1 1 0; padding: 8px 10px; border-radius: 12px; background: #1A1E28; font-size: 12px; color: #C6CBD8">Riverside Park</span><span style="flex: 1 1 0; padding: 8px 10px; border-radius: 12px; background: #1A1E28; font-size: 12px; color: #C6CBD8">14° · Light rain</span><span style="flex: 1 1 0; padding: 8px 10px; border-radius: 12px; background: #1A1E28; font-size: 12px; color: #C6CBD8">22,410 fans</span></div>
</section>

@@NAV@@
</div>
'''
BODY = BODY.replace("font-size: 16px: font-weight: 700; font-weight: 700", "font-size: 16px; font-weight: 700")

JS = r'''class Component extends DCLogic {
  renderVals() {
    const S = (nombre, h, a, dec) => {
      const t = h + a;
      const f = (v) => (dec ? v.toFixed(1) : String(v));
      return { nombre, h: f(h), a: f(a), wh: Math.round(h / t * 100), wa: Math.round(a / t * 100) };
    };
    return { stats: [S('Expected goals', 1.9, 0.8, true), S('Shots', 12, 6), S('On target', 6, 2), S('Big chances', 3, 1), S('Corners', 7, 3)] };
  }
}'''
page("Partido.dc.html", "Match", 390, 2260, BODY, JS, nav_active="m", tabs_active="Overview")
print("s1 ok")
