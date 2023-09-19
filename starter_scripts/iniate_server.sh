apt-get -y update
apt-get -y install freetds-dev freetds-bin
apt-get -y install pip
pip3 install --upgrade pip
pip3 install -r requirements.txt
apt-get -y install -y systemd
cd ~/brand-and-push-optimizador
[ -f ~/secrets.env ] && mv ~/secrets.env ~/brand-and-push-optimizador/secrets.env # move if exists
cp starter_scripts/systemd_app.service /etc/systemd/system/systemd_app.service
sudo systemctl daemon-reload
sudo systemctl enable systemd_app.service
sudo systemctl start systemd_app.service

#sudo apt-get -y install fail2ban # un poco pesado pero util si se reciben muchos ataques
#journalctl -u systemd_app.service > app_logs.txt  # this allow you to see logs of the running app
#ExecStart=/bin/bash -c 'cd /home/ubuntu/project/ && source env/bin/activate && python app.py'