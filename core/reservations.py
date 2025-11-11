# app/core/reservations.py
import json
import os
from datetime import datetime

def save_reservation(client: str, reservation: dict):
    """Guarda la reserva en clients/<client>/data/reservations.json"""
    base_path = f"clients/{client}/data"
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, "reservations.json")

    # Cargar reservas previas
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    reservation["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.append(reservation)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
