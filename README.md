# ta-source

## Local Development
```sh
cd frontend
npm install
npm install vue-router
npm install axios
npm install tailwindcss @tailwindcss/vite
npm run dev

cd backend
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt

alembic revision --autogenerate -m "Add new field"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Deployment
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
