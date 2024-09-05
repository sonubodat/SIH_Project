from pydantic import BaseModel


class LoadGood(BaseModel):
    name: str
    weight: int
    fragment: int
    source: int
    destination: int
    id:str

class Truck(BaseModel):
    name: str
    capacity: int
    phone_number: int
    truck_plate: str
    id:str


class get_order(BaseModel):
    id:str
    current_location:int
    capacity:int
    truck_id:str

class truck_arrive(BaseModel):
    truck_id:str
    