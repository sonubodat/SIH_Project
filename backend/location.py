from fastapi import FastAPI
import model
from pymongo import MongoClient


app = FastAPI()

MONGO_DETAILS = "mongodb://localhost:27017"  
client = MongoClient(MONGO_DETAILS)
database = client["SIH"]
truck_collection = database["trucks"]
load_fragment = database['load_fragment']
load = database['load']
shipment = database['shipment']
transit = database['transit']
completed=database['completed']


def update(id, collection, truck_id, weight, result):
    # Insert shipment information
    shipment.insert_one({'truck_id': truck_id, 'goods_id': id})
    # Update coming truck information in the specified collection
    collection['coming_truck'].insert_one({'truck_id': truck_id, 'weight': weight})
    # Insert transit information
    transit.insert_one(result)


def give_touch(id):
    # Map the id to the corresponding MongoDB collection
    if id == 1:
        return client['ahemdabad']
    elif id == 2:
        return client['gandhinagar']
    elif id == 3:
        return client['shamalaji']
    elif id == 4:
        return client['udaipur']
    else:
        return client['ajjmer']


def get_good(collection, weight, truck_id):
    fragment = collection['fragment']
    unfragment = collection['unfragment']

    # Check if the exact weight is available in the unfragmented collection
    result = unfragment.find_one({'weight': weight})
    message="hear is your unfragment goods"
    if result is not None:
        c = load.find_one({'id': result['id']})
        destination = c['destination']
        a = give_touch(destination)
        update(result['id'], a, truck_id, weight, result)
        unfragment.delete_one(result)
        return {
            'message':message,
            'id':result['id']
        }          

    # Fragmentation logic if no exact match is found
    q = weight // 10  # Use integer division here
    fragments = unfragment.find({'weight': 10}).limit(q)
    message="we all the goods whihch meets your requirment"
    id_queue = []
    for fragment_doc in fragments:
        
        c = load_fragment.find_one({'id': fragment_doc['id']})
        destination = c['destination']
        a = give_touch(destination)
        update(fragment_doc['id'], a, truck_id, 10, fragment_doc)
        id_queue.append(fragment_doc['id'])


    # Remove used fragments from unfragmented collection
    unfragment.delete_many({'id': {'$in': [doc['id'] for doc in fragments]}})
    
    return {
        'id_list':id_queue,
        'message':message
    }


@app.post("/goods", response_model=dict)
async def add_good(load_good: model.LoadGood):
    data = {
        'name': load_good.name,
        'source': load_good.source,
        'destination': load_good.destination,
        'weight': load_good.weight,
        'id': load_good.id,
        'fragment': load_good.fragment
    }
    load.insert_one(data)
    
    c = give_touch(load_good.source)
    
    if load_good.fragment == 0:
        c['unfragment'].insert_one({'weight': load_good.weight, 'id': load_good.id, 'destination': load_good.destination})
        return {"message": "The load is loaded on the unfragmented list"}
    
    # Fragmentation logic
    f = load_good.weight // 10  # Use integer division here
    d = 96  # ASCII value for 'a'
    for i in range(f):
        d += 1
        fragment_data = {
            'fragment_id': load_good.id + chr(d),
            'id': load_good.id,
            'weight': 10,
            'destination': load_good.destination
        }
        c['fragment'].insert_one(fragment_data)
        load_fragment.insert_one(fragment_data)
    
    return {"message": "The load is loaded into the fragment list"}


@app.post("/trucks", response_model=dict)
async def add_truck(truck: model.Truck):
    data = {
        'name': truck.name,
        'capacity': 100,
        'phone_number': truck.phone_number,
        'plat_number': truck.truck_plate,
        'id': truck.id
    }
    truck_collection.insert_one(data)
    return {"message": "Truck details are loaded"}


@app.post("/fetch_order", response_model=dict)
async def get_details(info: model.get_order):
    collections = give_touch(info.current_location)
    ids = get_good(collections, info.capacity, info.truck_id)
    if ids is None:
        return {"message": "There is no suitable weight available for this truck"}
    
    return id

@app.post("/delete",response_class=dict)
async def tuck_arrive(truck:model.truck_arrive):
    loads=transit.find({'truck_id':truck.truck_id})
    completed.insert_many(loads)
