import os
import requests
from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import UserInfo
from auth.utils import require_role

router = APIRouter(prefix="/sync", tags=["Sincronización"])

_cc = require_role("control_calidad")

@router.post(
    "/force",
    summary="Forzar Sincronización eSUM",
    description="Dispara manualmente el DAG de Airflow para sincronizar reportes.",
)
def force_sync(_user: UserInfo = Depends(_cc)):
    # Local Airflow info
    airflow_url = "http://airflow-webserver:8080/api/v1/dags/reprocesos_sync/dagRuns"
    # Fallback si se corre fuera de docker (localhost)
    # pero el backend está en docker, así que usa el nombre del servicio o host.docker.internal
    # El compose del backend no está en la misma network que airflow.
    # Airflow expone 8080 en la máquina host. Si backend está en otra red, usará host.docker.internal
    # Vamos a probar host.docker.internal primero, o la IP local.
    
    # Actually, from inside reprocesos_backend container (bridge network),
    # to access host's mapped port 8080, we use host.docker.internal.
    
    dag_url = "http://host.docker.internal:8080/api/v1/dags/reprocesos_sync/dagRuns"
    
    # Variables from env for Airflow
    user = os.environ.get("AIRFLOW_ADMIN_USER", "admin")
    pwd = os.environ.get("AIRFLOW_ADMIN_PASSWORD", "admin123")
    
    try:
        resp = requests.post(
            dag_url,
            json={"conf": {}},
            auth=(user, pwd),
            timeout=10
        )
        if resp.status_code == 200 or resp.status_code == 201:
            return {"detail": "Sincronización iniciada", "dag_run_id": resp.json().get("dag_run_id")}
        
        # fallback to direct IP if host.docker.internal fails (linux)
        # Assuming the backend container has access to 172.17.0.1 or similar
        raise Exception(f"Status {resp.status_code}: {resp.text}")
        
    except requests.exceptions.ConnectionError:
        # Retry with the container name if they are in the same network
        try:
            dag_url_alt = "http://airflow-webserver:8080/api/v1/dags/reprocesos_sync/dagRuns"
            resp2 = requests.post(
                dag_url_alt,
                json={"conf": {}},
                auth=(user, pwd),
                timeout=10
            )
            if resp2.status_code == 200 or resp2.status_code == 201:
                return {"detail": "Sincronización iniciada", "dag_run_id": resp2.json().get("dag_run_id")}
            raise Exception(f"Status {resp2.status_code}: {resp2.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo contactar a Airflow. Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disparando Airflow: {e}")
