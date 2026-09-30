import json, os
OUT = "/home/user/futbol-pipeline/app_apostador/diseno_nuevo/project"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>@@TITLE@@</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..900&amp;family=Instrument+Sans:wght@400;500;600;700&amp;display=swap">
<style>
body{margin:0;background:#0A0C11;font-family:"Instrument Sans",system-ui,sans-serif;color:#F1F3F8}
a{color:inherit;text-decoration:none}
button{font-family:inherit;cursor:pointer}
</style>
</helmet>
"""

def nav(active):
    items = [
        ("m", "Main.dc.html", "Matches", '<circle cx="12" cy="12" r="9"></circle><path d="M12 3v4M12 17v4M3 12h4M17 12h4"></path>'),
        ("e", "Elo.dc.html", "Ranking", '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"></path>'),
        ("t", "Tips.dc.html", "Tips", '<path d="M12 3l2.4 5.6 6.1.5-4.6 4 1.4 6-5.3-3.2-5.3 3.2 1.4-6-4.6-4 6.1-.5z"></path>'),
        ("f", "Equipo.dc.html", "Following", '<path d="M12 20s-7-4.4-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.6-7 10-7 10z"></path>'),
    ]
    out = ['<nav aria-label="Main" style="position: absolute; left: 16px; right: 16px; bottom: 18px; height: 64px; box-sizing: border-box; padding: 6px; border-radius: 32px; background: #161A23; border: 1px solid #2A3040; display: flex; align-items: center; justify-content: space-between">']
    for k, href, label, icon in items:
        on = k == active
        if on:
            out.append(f'<a href="{href}" aria-current="page" style="height: 50px; padding: 0 18px; border-radius: 25px; background: #4A63FF; color: #FFFFFF; display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{icon}</svg>{label}</a>')
        else:
            out.append(f'<a href="{href}" aria-label="{label}" style="width: 50px; height: 50px; border-radius: 25px; color: #8E96AA; display: flex; align-items: center; justify-content: center"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></a>')
    out.append('</nav>')
    return "\n".join(out)

def tabs(active, links):
    names = ["Overview", "Stats", "Lineups", "H2H", "Tips"]
    parts = ['<nav aria-label="Match sections" style="display: flex; gap: 24px; padding: 0 16px; border-bottom: 1px solid #232838">']
    for n in names:
        on = n == active
        cur = 'aria-current="page"' if on else ''
        line = "#C8FF3D" if on else "transparent"
        col = "#F1F3F8" if on else "#8E96AA"
        parts.append('<a href="%s" %s style="height: 46px; display: flex; align-items: center; border-bottom: 3px solid %s; color: %s; font-size: 14px; font-weight: 700; white-space: nowrap">%s</a>' % (links.get(n, "#"), cur, line, col, n))
    parts.append('</nav>')
    return "\n".join(parts)

MATCH_LINKS = {"Overview": "Partido.dc.html", "Stats": "Stats.dc.html", "Lineups": "Alineacion.dc.html", "Tips": "Tips.dc.html"}

def page(fname, title, w, h, body, js, nav_active=None, tabs_active=None):
    b = body
    if nav_active:
        b = b.replace("@@NAV@@", nav(nav_active))
    else:
        b = b.replace("@@NAV@@", "")
    if tabs_active:
        b = b.replace("@@TABS@@", tabs(tabs_active, MATCH_LINKS))
    src = HEAD.replace("@@TITLE@@", title) + b + "\n</x-dc>\n" + \
        '<script type="text/x-dc" data-dc-script data-props=\'{"$preview":{"width":%d,"height":%d}}\'>\n' % (w, h) + js + "\n</script>\n</body>\n</html>\n"
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, fname), "w").write(src)

CSS_DISP = "font-family: 'Archivo', sans-serif; font-stretch: 75%; font-weight: 800"
