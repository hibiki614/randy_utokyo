import folium
import csv
from glob import glob
from datetime import datetime as dt
from datetime import timedelta as td
from zoneinfo import ZoneInfo
import timestamped_geo_json_custom
from re import sub

def select_file(s=''):
    filenames=glob('vpos*'+s+'*_ext_*.csv')
    cropped=[e[:-13] for e in filenames]
    distinct=[e for r,e in enumerate(cropped) if e not in cropped[:r]]
    print('\nSelect file\n'+'\n'.join(['\t'+str(k)+' : '+fn for k,fn in enumerate(distinct)])+'\n')
    return [distinct[i] for i in range(int(input('From = ')),int(input('To = '))+1)]

def type_color_weight(type):
	if type=='I_09_1204235410434':
		return ('blue',5)
	return ('black',3)

def animated_vehicles(name):
	vids=[]
	types=[]
	points=[]
	times=[]
	with open(name, 'r', newline='', encoding='utf-8') as rfile:
		csvfile = csv.DictReader(rfile)
		for row in csvfile:
			vid=row["VID"]
			point=[float(row["Pos.x"]),float(row["Pos.y"])]
			time='2025-01-01T'+row["Time"]
			if vids.count(vid)==0:
				vids.append(vid)
				types.append(row["Type"])
				points.append([point])
				times.append([time])
			else:
				i=vids.index(vid)
				points[i].append(point)
				times[i].append(time)
	features=[]
	for k,vid in enumerate(vids):
		c,w=type_color_weight(types[k])
		features.append(
			{
				"type": "Feature",
				"geometry": {
					"type": "LineString",
					"coordinates": [points[k][0]]*2,
				},
				"properties": {
					"times": [times[k][0]]*2,
					"popup": vid,
					"tooltip": vid,
					"style": {
						"color": c,
						"weight": w,
					},
				},
			}
		)
		for i in range(1,len(times[k])):
			features.append(
				{
					"type": "Feature",
					"geometry": {
						"type": "LineString",
						"coordinates": points[k][i-1:i+1],
					},
					"properties": {
						"times": [times[k][i]]*2,
						"popup": vid,
						"tooltip": vid,
						"style": {
							"color": c,
							"weight": w,
						},
					},
				}
			)
	return features


def times_range(a):
	b=[]
	for seg in a:
		start_time=dt(seg[0],seg[1],seg[2],seg[3],seg[4],tzinfo=ZoneInfo("Asia/Tokyo")).timestamp()
		end_time=dt(seg[5],seg[6],seg[7],seg[8],seg[9],tzinfo=ZoneInfo("Asia/Tokyo")).timestamp()
		t=start_time
		while t<=end_time:
			b.append(int(t*1000))
			t+=1
	return b

segments=['0600-0700','0700-0800','0800-0900','0900-1000','1000-1100','1100-1200','1200-1300','1300-1400','1400-1500','1500-1600','1600-1700','1700-1800','1800-1900']
hours=[6,7,8,9,10,11,12,13,14,15,16,17,18]

def display_vehicles():
	for prefix in select_file():
		for h,seg in zip(hours,segments):
			m=folium.Map(location=[35.89761660739192, 139.9451633887103], tiles="cartodbpositron", zoom_start=17)
			if h==6:
				day_range=[[2025,1,1,6,30,2025,1,1,7,0]]
			else:
				day_range=[[2025,1,1,h,0,2025,1,1,h+1,0]]
			timestamped_geo_json_custom.TimestampedGeoJson({"type": "FeatureCollection", "features": animated_vehicles(prefix+seg+'.csv')}, times_range(day_range), duration="PT1S").add_to(m)
			m.save(prefix+seg+'.html')

display_vehicles()