#!/bin/bash
cd /home/Dragon_Slayer/projects/weather-collector
source venv/bin/activate
python -c "
import pymongo
import json
from dotenv import load_dotenv
import os
load_dotenv()
client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
db = client['weather_db']
collection = db['weather_data']
records = list(collection.find().sort([('_id', -1)]).limit(100))
for r in records:
    r['_id'] = str(r['_id'])
with open('/home/Dragon_Slayer/Downloads/frontend/src/data/real_data.json', 'w') as f:
    json.dump({'records': records}, f, indent=2, default=str)
print('Frontend data updated')
"
