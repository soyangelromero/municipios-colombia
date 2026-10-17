from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':900})
    page.goto('http://localhost:8765/', wait_until='networkidle')
    page.wait_for_timeout(500)
    info = page.evaluate("""() => {
      const mseg = document.querySelector('.mseg');
      const btn = mseg?.querySelector('[aria-pressed="true"]');
      const th = mseg?.querySelector('.mseg__th');
      return {
        intro: !!document.querySelector('.intro'),
        conIntro: document.documentElement.classList.contains('con-intro'),
        msegRect: mseg?.getBoundingClientRect().toJSON(),
        btnRect: btn?.getBoundingClientRect().toJSON(),
        btnOffsetLeft: btn?.offsetLeft,
        thLeft: th?.style.left,
        thWidth: th?.style.width,
        thOffsetParent: th?.offsetParent?.className,
      };
    }""")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    browser.close()
PY