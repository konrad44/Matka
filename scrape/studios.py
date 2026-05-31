import json, urllib.request, urllib.parse, time

studios = [
  {"name":"Flexora Studio Pole Dance","addr":"Helska 8, Gdynia","url":"https://www.flexorastudiopoledance.pl/"},
  {"name":"Pole Dance Academy","addr":"aleja Zwycięstwa 197, Gdynia","url":"https://www.trojmiasto.pl/Pole-Dance-Academy-o49158.html"},
  {"name":"Panther Dance","addr":"Podgórska 1, Gdynia","url":"https://www.panther-dance.com/"},
  {"name":"Lekko Studio Pole Dance","addr":"Wielkopolska 395, Gdynia","url":"https://www.facebook.com/p/Lekko-Studio-Pole-Dance-w-Gdyni-100063900489574/"},
  {"name":"Dance Fusion","addr":"Tadeusza Wendy 7/9, Gdynia","url":"https://www.trojmiasto.pl/"},
  {"name":"Lejdis Studio Gdynia","addr":"Władysława IV 51, Gdynia","url":"https://gdynia.lejdisstudio.com/"},
]
def geo(q):
    u="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":q,"format":"json","limit":1,"countrycodes":"pl"})
    r=urllib.request.Request(u,headers={"User-Agent":"gdynia-map/1.0 (klepacki1492@gmail.com)"})
    d=json.load(urllib.request.urlopen(r,timeout=30))
    return d
out=[]
for s in studios:
    res=geo(s["addr"])
    if not res:
        res=geo(s["name"]+", Gdynia")
    if res:
        s["lat"]=float(res[0]["lat"]); s["lon"]=float(res[0]["lon"])
        s["geocoded"]=res[0].get("display_name","")
    else:
        s["lat"]=None; s["lon"]=None
    print(s["name"], s.get("lat"), s.get("lon"))
    out.append(s); time.sleep(1.1)
json.dump(out, open("data/_studios_raw.json","w"), ensure_ascii=False, indent=2)
