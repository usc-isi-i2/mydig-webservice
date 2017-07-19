#!/bin/sh
cd ws/
python ws.py --dummy-this-is-mydig-backend
cd ..

cd frontend
python service.py --dummy-this-is-mydig-frontend
cd ..