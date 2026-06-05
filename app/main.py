from fastapi import FastAPI
from pydantic import BaseModel
from app.database import engine, SessionLocal
from app.models import Base, Shipment
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge


app = FastAPI(
        title="ColdChain Risk Monitor",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)
Instrumentator().instrument(app).expose(app)

total_orders_gauge = Gauge(
    "coldchain_total_orders",
    "Total number of unique orders"
)

total_shipments_gauge = Gauge(
    "coldchain_total_shipments",
    "Total number of shipments"
)

low_risk_gauge = Gauge(
    "coldchain_low_risk_shipments",
    "Total number of low risk shipments"
)

medium_risk_gauge = Gauge(
    "coldchain_medium_risk_shipments",
    "Total number of medium risk shipments"
)

high_risk_gauge = Gauge(
    "coldchain_high_risk_shipments",
    "Total number of high risk shipments"
)

high_risk_orders_gauge = Gauge(
    "coldchain_orders_with_high_risk",
    "Total number of orders with at least one high risk shipment"
)


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

def update_business_metrics():

    db = get_db()
    shipments = db.query(Shipment).all()

    total_shipments = len(shipments)
    total_orders = len(set(shipment.order_id for shipment in shipments))

    low_risk = 0
    medium_risk = 0
    high_risk = 0
    high_risk_orders = set()

    for shipment in shipments:
        risk = calculate_risk(shipment.temperature)

        if risk == "LOW":
            low_risk += 1

        elif risk == "MEDIUM":
            medium_risk += 1

        else:
            high_risk += 1
            high_risk_orders.add(shipment.order_id)

    total_orders_gauge.set(total_orders)
    total_shipments_gauge.set(total_shipments)
    low_risk_gauge.set(low_risk)
    medium_risk_gauge.set(medium_risk)
    high_risk_gauge.set(high_risk)
    high_risk_orders_gauge.set(len(high_risk_orders))

    db.close()


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

    update_business_metrics()

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

@app.get("/business-metrics-refresh")
def refresh_business_metrics():
    update_business_metrics()

    return {
        "message": "Business metrics updated successfully"
    }