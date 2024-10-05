1)
cd ./backend/api
npm run setup

2)
mprocs --config ./mprocs.yml

sudo ufw allow 8000


--rocky linux
sudo dnf install firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

ssh -L 8000:localhost:8000 pfavvatas@BCM