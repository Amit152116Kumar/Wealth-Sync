from fastapi.testclient import TestClient
from fastapi import status
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    
def test_subscribe():
    response = client.get("/subscribe")
    assert response.status_code == status.HTTP_200_OK

def test_unsubscribe():
    response = client.get("/unsubscribe")
    assert response.status_code == status.HTTP_200_OK
    
def test_orders():
    response = client.get("/orders")
    assert response.status_code == status.HTTP_200_OK
    
def test_trades():
    response = client.get("/trades")
    assert response.status_code == status.HTTP_200_OK

def test_funds():
    response = client.get("/funds")
    assert response.status_code == status.HTTP_200_OK
