# site76 (index.html + a/*) -> the GitHub Pages / installable-app (PWA) version.
# usage: python3 mk_web.py <site dir> <repo dir> <icon.ico>
import re, sys, os, shutil, json
from PIL import Image
SITE, REPO, ICO = sys.argv[1:4]
s = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
m = re.search(r"const BUILD='(v\d+)'", s); BUILD = m.group(1)
# keep the repo's .git, replace everything else
for n in os.listdir(REPO):
    if n in ('.git',): continue
    p = os.path.join(REPO, n)
    shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
shutil.copytree(os.path.join(SITE, 'a'), os.path.join(REPO, 'a'))
# icons from the largest size inside the .ico
ic = Image.open(ICO); sizes = ic.info.get('sizes') or {ic.size}
big = max(sizes); ic.size = big; base = ic.convert('RGBA'); print('icon source', big)
os.makedirs(os.path.join(REPO, 'icons'))
for n in (180, 192, 512):
    base.resize((n, n), Image.LANCZOS).save(os.path.join(REPO, 'icons', 'icon-%d.png' % n))
# maskable (safe-zone padded) 512
pad = Image.new('RGBA', (512, 512), (255, 255, 255, 0)); k = base.resize((384, 384), Image.LANCZOS); pad.paste(k, (64, 64), k)
pad.save(os.path.join(REPO, 'icons', 'icon-maskable-512.png'))
json.dump({
  'name': 'קלארק', 'short_name': 'קלארק', 'lang': 'he', 'dir': 'rtl',
  'start_url': './', 'scope': './', 'id': './',
  'display': 'standalone', 'display_override': ['fullscreen', 'standalone'],
  'orientation': 'any', 'background_color': '#000000', 'theme_color': '#000000',
  'icons': [
    {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
    {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
    {'src': 'icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]
}, open(os.path.join(REPO, 'manifest.webmanifest'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
inject = ('<link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#000000">'
          '<link rel="apple-touch-icon" href="icons/icon-180.png"><meta name="apple-mobile-web-app-capable" content="yes">'
          '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="קלארק">'
          '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
          '<script>if("serviceWorker" in navigator&&(location.protocol==="https:"||location.hostname==="localhost"))addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){})})</script>')
assert s.count('<title>') == 1
out = s.replace('<title>', inject + '<title>', 1)
open(os.path.join(REPO, 'index.html'), 'w', encoding='utf-8').write(out)
# service worker: pictures/sounds (hash-named, never change) cache-first; the page itself network-first
sw = """const C='clark-%s';
self.addEventListener('install',e=>{self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C&&k!=='clark-a').map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
 const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;
 if(/\\/a\\/[0-9a-f]{12}\\./.test(u.pathname)){
  e.respondWith(caches.open('clark-a').then(c=>c.match(r).then(h=>h||fetch(r).then(n=>{if(n.ok)c.put(r,n.clone());return n}))));return}
 e.respondWith(fetch(r,{cache:'no-store'}).then(n=>{if(n.ok){const cp=n.clone();caches.open(C).then(c=>c.put(r,cp))}return n}).catch(()=>caches.match(r,{ignoreSearch:true})));
});
""" % BUILD
open(os.path.join(REPO, 'sw.js'), 'w').write(sw)
json.dump({'build': BUILD}, open(os.path.join(REPO, 'version.json'), 'w'))
open(os.path.join(REPO, '.nojekyll'), 'w').write('')
open(os.path.join(REPO, 'README.md'), 'w', encoding='utf-8').write('# קלארק\n\nמשחק לילדים. נפתח בדפדפן ואפשר להתקין כאפליקציה (הוסף למסך הבית / התקן).\n\nבניית הגרסה: %s\n' % BUILD)
print('web build', BUILD, 'ok')
