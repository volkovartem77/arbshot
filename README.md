# ArbShot. Deploy on server Ubuntu 22.04 (DigitalOcean 4GB/4CPU)

### Install Python 3.10.4

**Make sure that you are logged in as root**

```
sudo apt-get update
sudo apt install -y python3-pip
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### Install Git, ArbShot

Git
```
apt-get install git-core -y
git clone https://github.com/volkovartem77/arbshot.git
```

Memcached
```
sudo apt install -y memcached
sudo apt install -y libmemcached-tools
sudo systemctl start memcached
```

Supervisor
```
apt-get install supervisor -y
mkdir /var/log/arbshot
cp ~/arbshot/flask_server.conf /etc/supervisor/conf.d/flask_server.conf
cp ~/arbshot/arbshot.conf /etc/supervisor/conf.d/arbshot.conf
mkdir /root/arbshot/supervisor
supervisorctl update
```

### Creating virtualenv using Python 3.10.4

```
pip install virtualenv
virtualenv -p /usr/bin/python3 ~/arbshot/venv
cd ~/arbshot; . venv/bin/activate
pip install -r requirements.txt
python3 configure.py
deactivate
```

### Start server
```
supervisorctl status
supervisorctl start flask_server
supervisorctl start streamBinanceSpot
supervisorctl start monitoring
supervisorctl status
```

