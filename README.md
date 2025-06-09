0)
```sh
sudo apt update
sudo apt install nodejs npm
node -v
npm -v
npm install -g mprocs
sudo apt install python3-venv
sudo apt-get install chromium-chromedriver
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt update
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

1)
```sh
cd ./backend/api
npm install scripty --save-dev
npm run setup
```

2)
```sh
cd ./backend/server
npm run setup
```

3)
```sh
cd ./frontend
npm run setup
```

4) Run the projects:
```sh
export CHROME_BINARY=/opt/google/chrome/google-chrome
mprocs --config ./mprocs.yml
```




========================================================
sudo ufw allow 8000


--rocky linux
sudo dnf install firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

ssh -L 8000:localhost:8000 pfavvatas@BCM



Urls:
https://knlcstbpuj.com/3hdblwjs
https://vwfakboihm.com/g45xrqf8
https://sdzmgpqimk.com/8bmcw52l
https://elxbturwnx.com/q3xjcvfi
https://zcnuqtmsan.com/t6pyrkq2
https://mivkubpwbl.com/y92lxtwv
https://dlsivpwgto.com/bpgf5z1n
https://rshfltonic.com/5ctfnxyo
https://yvucrxdoqs.com/n39zwgy8
https://lopmcvkdxy.com/p7k49g2j
https://zkndoqrbci.com/dw7ghf4x
https://ksdmjoxvwl.com/k9xfwjq2
https://quxopdjftw.com/whg52lv1
https://yfpaxhgkti.com/qjtvnm4p
https://wlbrjydmxk.com/z32fnb79
https://rblvtmkqsx.com/tc91f83o
https://cuazrkmdnl.com/xph5v2qw
https://bzrhtonyqj.com/pv7krn2c
https://mnxrbhfjtl.com/83cstvpq
https://wykgtmjose.com/vr49tjgx
https://ycxyqmmxes.com/0fpxjfbo
https://bfiroukswf.com/pdi7l4tg
https://tatyzgcdfc.com/7tr6qfdl
https://qjuunldndc.com/3e3yblvb
https://zxztqxrmgg.com/o9f54drp
https://mzpozdoqgq.com/0bvme0m9
https://gubgcrhvrc.com/242lmmnp
https://foljsqvlzm.com/wkgff8oy
https://apygzbcvpx.com/vfe5ko5n
https://uyzthowgoy.com/y44d48ol
https://xpfwdkpbgn.com/p37vlhd7
https://jpibouhgkt.com/27pv7rqx
https://mcbpzdiyeh.com/vtmrq1vm
https://qcyqzogijt.com/cgn21vh1
https://ioxoosjdgt.com/bfreonsc
https://aobwulytug.com/yl7totju
https://eeyxzzycwm.com/tyvb2s58
https://muukiclxbn.com/zn6q6kxq
https://zmsxphkhhh.com/9ggxxz2n
https://uovsrphcpj.com/umc2m8zd ​


https://nvd.nist.gov/vuln/detail/CVE-2020-14624
https://nvd.nist.gov/vuln/detail/CVE-2018-5032
http://jvn.jp/en/jp/JVN41119755/index.html
http://jvn.jp/en/jp/JVN33214411/index.html
https://www.kb.cert.org/vuls/id/366027
https://www.kb.cert.org/vuls/id/229438


https://akispetretzikis.com/recipe/7817/mpakaliaros-me-prasa

https://akispetretzikis.com/en/recipe/7817/mpakaliaros-me-prasa



#TEST
file:///home/pfavvatas/lib_url_to_img/test/test1.html


https://security.gentoo.org/glsa/202105-27 No Types Assigned

Étienne Gervais, Charl-Alexandre Le Brun and Chatwork Co., Ltd. reported this vulnerability to Six Apart Ltd. and coordinated. 

# WSL (Windows Subsystem for Linux) Setup Instructions

If you are running this project in WSL (Windows Subsystem for Linux), follow these steps to ensure Google Chrome and ChromeDriver work correctly with Selenium:

## 1. Install Google Chrome in WSL

```sh
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt update
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

## 2. Install ChromeDriver (matching your Chrome version)

1. Check your Chrome version:
   ```sh
   /opt/google/chrome/google-chrome --version
   ```
2. Download the matching ChromeDriver from:
   https://googlechromelabs.github.io/chrome-for-testing/
3. Unzip and move it to your PATH:
   ```sh
   sudo apt install unzip
   wget <chromedriver-zip-url>
   unzip chromedriver-linux64.zip
   sudo mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
   sudo chmod +x /usr/bin/chromedriver
   chromedriver --version  # Should match Chrome version
   ```

## 3. Install required dependencies

Some libraries are needed for Chrome to run in headless mode:
```sh
sudo apt-get install -y libnss3 libxi6 libxcursor1 libxdamage1 libxrandr2 libatk1.0-0 libcups2t64 libdbus-1-3 libgtk-3-0t64 libxcomposite1 libxss1 libxtst6 fonts-liberation libappindicator3-1 xdg-utils
```

## 4. Set the Chrome binary path (optional but recommended)

Add this to your shell before running the project:
```sh
export CHROME_BINARY=/opt/google/chrome/google-chrome
```

## 5. Use a Python virtual environment

```sh
python3 -m venv venv
source venv/bin/activate
pip install selenium
```

## 6. Troubleshooting

- If you see `no chrome binary at ...` errors, double-check the Chrome and ChromeDriver versions match and that `/opt/google/chrome/google-chrome` exists and is executable.
- If you see `ModuleNotFoundError: No module named 'selenium'`, make sure your virtual environment is activated.
- If you see errors about missing libraries, re-run the dependencies install command above.
- If you are using WSL1 and have issues, consider upgrading to WSL2 for better compatibility with headless browsers.

---

## Python Dependencies for Clustering

To use the clustering features, you need to install several Python packages. Make sure your virtual environment is activated (see step 5 above), then run:

```sh
pip install -r lib_url_to_img/backend/requirements.txt
```

**Note:** If you see an error like `ModuleNotFoundError: No module named 'colormath'`, double-check that your virtual environment is activated. You can activate it with:

```sh
source venv/bin/activate
```

If you encounter issues with the `dbcv` package (not available on PyPI), it will be installed from source via the requirements file. If you need to install it manually, you can run:

```sh
pip install git+https://github.com/scikit-learn-contrib/hdbscan.git
```

This will install `hdbscan` and the bundled `dbcv` implementation.

---