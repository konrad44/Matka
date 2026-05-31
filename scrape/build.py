import json, math, urllib.request, urllib.parse, time
from datetime import date

def hav(a,b,c,d):
    R=6371000; p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

# ---- SKM stops ----
raw=json.load(open("data/_skm_raw.json"))
SKM_NAMES=["Gdynia Główna","Gdynia Stocznia - Uniwersytet Morski",
  "Gdynia Wzgórze Świętego Maksymiliana","Gdynia Redłowo","Gdynia Orłowo",
  "Gdynia Grabówek","Gdynia Leszczynki","Gdynia Cisowa","Gdynia Chylonia"]
by={}
for e in raw:
    n=e["name"]
    if n not in SKM_NAMES: continue
    score=2 if "SKM" in (e.get("network","")+e.get("operator","")) else (1 if e["railway"]=="halt" else 0)
    if n not in by or score>by[n][0]:
        by[n]=(score,e)
skm=[{"name":k,"lat":v[1]["lat"],"lon":v[1]["lon"]} for k,v in by.items()]
skm.sort(key=lambda s:s["lat"])
print("SKM stops:",len(skm))
for s in skm: print("  ",s["name"])

# ---- Studios ----
studios=[s for s in json.load(open("data/_studios_raw.json")) if s.get("lat")]
for s in studios:
    s["nearestSkm"]=min(skm,key=lambda k:hav(s["lat"],s["lon"],k["lat"],k["lon"]))["name"]
    s["nearestSkmDist"]=round(min(hav(s["lat"],s["lon"],k["lat"],k["lon"]) for k in skm))
print("Studios:",len(studios))

# ---- Apartments ----
det=json.load(open("data/_otodom_detail.json"))
def geo(q):
    u="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":q,"format":"json","limit":1,"countrycodes":"pl"})
    r=urllib.request.Request(u,headers={"User-Agent":"gdynia-map/1.0 (klepacki1492@gmail.com)"})
    try: return json.load(urllib.request.urlopen(r,timeout=30))
    except: return []
for d in det:
    if not d.get("lat"):
        q=", ".join(x for x in [d.get("street"),d.get("district"),"Gdynia"] if x)
        res=geo(q) or geo((d.get("district") or "")+", Gdynia")
        if res: d["lat"]=float(res[0]["lat"]); d["lon"]=float(res[0]["lon"]); d["coordSource"]="nominatim"
        time.sleep(1.1)
apts=[]
for d in det:
    if not d.get("lat"): continue
    dist=min(hav(d["lat"],d["lon"],k["lat"],k["lon"]) for k in skm)
    near=min(skm,key=lambda k:hav(d["lat"],d["lon"],k["lat"],k["lon"]))
    d["nearestSkm"]=near["name"]; d["nearestSkmDist"]=round(dist)
    if dist<=1500: apts.append(d)
apts.sort(key=lambda a:a["nearestSkmDist"])
print("Apartments >=80m2 total geocoded:",len([d for d in det if d.get('lat')]),"within 1.5km:",len(apts))

out={"generatedAt":str(date.today()),
     "skm":skm,"studios":studios,"apartments":apts}
json.dump(out,open("data/data.json","w"),ensure_ascii=False,indent=2)
open("data/data.js","w").write("window.MAP_DATA = "+json.dumps(out,ensure_ascii=False,indent=2)+";\n")
print("WROTE data/data.json and data/data.js")
