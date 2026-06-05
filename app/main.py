from fastapi import FastAPI
from pydantic import BaseModel
from app.database import engine, SessionLocal
from app.models import Base, Shipment
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(
        title="ColdChain Risk Monitor",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)
Instrumentator().instrument(app).expose(app)

# Modelo de datos


class TemperatureReading(BaseModel):
    order_id: str
    shipment_id: str
    product_type: str
    temperature: float


# Base de datos temporal (lista en memoria)

def get_db():
    return SessionLocal()

def calculate_risk(temperature: float):

    if temperature <= 8:
        return "LOW"

    elif temperature <= 10:
        return "MEDIUM"

    return "HIGH"


@app.get("/")
def root():
    return {
        "message": "ColdChain Risk Monitor API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/temperature")
def add_temperature(reading: TemperatureReading):

    db = get_db()

    shipment = Shipment(
        order_id=reading.order_id,
        shipment_id=reading.shipment_id,
        product_type=reading.product_type,
        temperature=reading.temperature

    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    db.close()

    return {
        "message": "Temperature registered successfully",
        "shipment_id": shipment.shipment_id
    }

@app.get("/shipments")
def get_shipments():

    db = get_db()

    shipments = db.query(Shipment).all()

    db.close()

    return shipments

@app.get("/risk/{shipment_id}")
def get_risk(shipment_id: str):

    db = get_db()

    shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )

    db.close()

    if shipment:

        return {
            "shipment_id": shipment.shipment_id,
            "temperature": shipment.temperature,
            "risk": calculate_risk(shipment.temperature)
        }

    return {
        "error": "Shipment not found"
    }