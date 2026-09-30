from common import *
from logo import *

W, H = 880, 1240
card = "border-radius: 28px; display: flex; align-items: center; justify-content: center"
body = f'''
<div style="width: {W}px; height: {H}px; box-sizing: border-box; padding: 48px; background: #0A0C11; display: flex; flex-direction: column; gap: 24px">

<div style="height: 420px; {card}; background: #12151C; border: 1px solid #232838; position: relative; overflow: hidden">
<span style="position: absolute; left: 50%; top: 50%; width: 460px; height: 300px; margin: -150px 0 0 -230px; border-radius: 50%; background: #FFD21F; opacity: 0.10; filter: blur(80px)"></span>
<div style="position: relative; display: flex; align-items: center; gap: 22px">{icono(150, "big")}{palabra(118)}</div>
</div>

<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px">
<div style="height: 250px; {card}; background: #12151C; border: 1px solid #232838; flex-direction: column; gap: 18px">
<div style="width: 120px; height: 120px; border-radius: 30px; background: #0A0C11; border: 1px solid #2A3040; display: flex; align-items: center; justify-content: center; box-shadow: 0 16px 40px rgba(0,0,0,0.5)">{icono(96, "app")}</div>
<span style="font-size: 13px; color: #8E96AA">App icon</span>
</div>
<div style="height: 250px; {card}; background: #FFD21F; flex-direction: column; gap: 18px">
<div style="width: 120px; height: 120px; border-radius: 30px; background: #FFD21F; border: 2px solid #0A0C11; display: flex; align-items: center; justify-content: center">{icono(96, "inv", fondo="#FFD21F", amarillo="#0A0C11", rojo="#FF3B3B")}</div>
<span style="font-size: 13px; font-weight: 600; color: #0A0C11">On yellow</span>
</div>
<div style="height: 250px; {card}; background: #12151C; border: 1px solid #232838; flex-direction: column; gap: 22px">
<div style="display: flex; align-items: flex-end; gap: 22px">{icono(64, "s64")}{icono(40, "s40")}{icono(24, "s24")}{icono(16, "s16")}</div>
<span style="font-size: 13px; color: #8E96AA">Small sizes</span>
</div>
</div>

<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px">
<div style="height: 170px; {card}; background: #F4F2EC">
<div style="display: flex; align-items: center; gap: 12px">{icono(64, "light", fondo="#F4F2EC")}{palabra(52, color="#0A0C11", dos="#E0A800")}</div>
</div>
<div style="height: 170px; {card}; background: #12151C; border: 1px solid #232838; flex-direction: column; gap: 14px">
{palabra(64)}
<span style="font-size: 13px; color: #8E96AA">Wordmark only</span>
</div>
</div>

<div style="display: flex; gap: 16px; align-items: center">
<span style="width: 56px; height: 56px; border-radius: 16px; background: #FFD21F"></span>
<div style="display: flex; flex-direction: column; gap: 2px; width: 150px"><span style="font-size: 14px; font-weight: 700; color: #F1F3F8">Card yellow</span><span style="font-size: 12px; color: #8E96AA">#FFD21F</span></div>
<span style="width: 56px; height: 56px; border-radius: 16px; background: #FF3B3B"></span>
<div style="display: flex; flex-direction: column; gap: 2px; width: 150px"><span style="font-size: 14px; font-weight: 700; color: #F1F3F8">Sent-off red</span><span style="font-size: 12px; color: #8E96AA">#FF3B3B</span></div>
<span style="width: 56px; height: 56px; border-radius: 16px; background: #0A0C11; border: 1px solid #2A3040"></span>
<div style="display: flex; flex-direction: column; gap: 2px; width: 150px"><span style="font-size: 14px; font-weight: 700; color: #F1F3F8">Night</span><span style="font-size: 12px; color: #8E96AA">#0A0C11</span></div>
</div>
</div>
'''
page("Logo.dc.html", "2yellow logo", W, H, body, "class Component extends DCLogic {\n  renderVals() { return {}; }\n}")
print("logo ok")
