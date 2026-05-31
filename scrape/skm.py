import json, urllib.request, urllib.parse

QUERY = """
[out:json][timeout:60];
area["name"="Gdynia"]["admin_level"="6"]->.g;
(
  node["railway"~"station|halt"](area.g);
);
out body;
"""
data = urllib.parse.urlencode({"data": QUERY}).encode()
req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data,
    headers={"User-Agent":"gdynia-map/1.0"})
res = json.load(urllib.request.urlopen(req, timeout=90))
stops=[]
for e in res["elements"]:
    t=e.get("tags",{})
    name=t.get("name","")
    if "Gdynia" not in name: continue
    stops.append({"name":name,"lat":e["lat"],"lon":e["lon"],
                  "railway":t.get("railway"),"network":t.get("network",""),"operator":t.get("operator","")})
stops.sort(key=lambda s:s["name"])
for s in stops: print(s["railway"], s["name"], s.get("network"), s.get("operator"))
print("TOTAL", len(stops))
json.dump(stops, open("data/_skm_raw.json","w"), ensure_ascii=False, indent=2)
