# ta-source
A web-based system for teaching assistants and students to efficiently review homework logs.
![Main Page](https://github.com/user-attachments/assets/958fffa9-6eca-4269-91e5-e58950271059)

## Quick Start

### Frontend Setup
```sh
cd frontend
npm install
npm run dev
```

### Backend Setup
```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Setup
```sh
cd backend
# alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

## Features
- OAuth Login (NYCU/CSIT)
- Log Management System
- Role-based Access

## Tech Stack
- Frontend: Vue.js
- Backend: FastAPI
- Database: MySQL

## Deployment Instructions
```sh
sudo su -
cd /var/www
git clone --recursive git@github.com:gainsborouo/ta-source.git
cd ta-source
chown -R www-data:www-data /var/www/ta-source
chmod -R 755 /var/www/ta-source

cd frontend
npm install
npm run build

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

chown -R www-data:www-data /var/www/ta-source/backend/.venv

vim /etc/systemd/system/ta-backend.service
systemctl daemon-reload
systemctl enable ta-backend.service
systemctl start ta-backend.service
systemctl status ta-backend.service

vim /etc/nginx/sites-available/ta.conf
ln -s /etc/nginx/sites-available/ta.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
systemctl status nginx

git config --global --add safe.directory /var/www/ta-source
```
