from playwright.sync_api import sync_playwright
import json
errors=[]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':900})
    page.on('console', lambda m: errors.append(m.text) if m.type=='error' else None)
    page.goto('http://localhost:8765/', wait_until='networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path='D:/Proyectos/Municipios Colombia/e2e/capturas/current-home.png', full_page=False)
    info = page.evaluate("""() => ({
      introVisible: !!document.querySelector('.intro')?.offsetParent,
      heroText: document.querySelector('.hero__h1')?.innerText,
      mapaDato: document.querySelector('.mapa__dato')?.getBoundingClientRect().toJSON(),
      leyenda: document.querySelector('.leyenda-card')?.getBoundingClientRect().toJSON(),
      topSolid: document.querySelector('.top')?.classList.contains('solid'),
      msegTh: document.querySelector('.mseg__th')?.getBoundingClientRect().toJSON(),
    })""")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print('console errors:', errors)
    browser.close()
