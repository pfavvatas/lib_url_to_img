0)
```sh
sudo apt update
sudo apt install nodejs npm
node -v
npm -v
npm install -g mprocs
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

https://nvd.nist.gov/vuln/detail/CVE-2020-14624
https://nvd.nist.gov/vuln/detail/CVE-2018-5032
http://jvn.jp/en/jp/JVN41119755/index.html
http://jvn.jp/en/jp/JVN33214411/index.html
https://www.kb.cert.org/vuls/id/366027
https://www.kb.cert.org/vuls/id/229438
https://www.dia-trofis.gr/lifestyle/vassilopita-i-tixeri-apo-ton-ilia-mamalaki/
https://www.dia-trofis.gr/lifestyle/pos-den-tha-ksefigete-tis-imeres-tou-pasxa/
https://www.gastronomos.gr/syntagh/spitika-kraker-me-paprika/313344/
https://www.gastronomos.gr/syntagh/koyloyrakia-kakaoy-nistisima-choris-anamoni/313773/


#TEST
file:///home/pfavvatas/lib_url_to_img/test/test1.html


https://security.gentoo.org/glsa/202105-27 No Types Assigned

Étienne Gervais, Charl-Alexandre Le Brun and Chatwork Co., Ltd. reported this vulnerability to Six Apart Ltd. and coordinated.


# 🧪 CACHE OPTIMIZATION TEST URLS

## Quick Test URLs (Ready to Copy-Paste)

### 🎯 Cross-Domain Test (3 URLs - Different Domains)
```
https://github.com/features
https://stackoverflow.com/questions
https://developer.mozilla.org/en-US/docs/Web/HTML
```

### 🎯 GitHub Only Test (3 URLs - Same Domain)
```
https://github.com/features
https://github.com/pricing
https://github.com/enterprise
```

### 🎯 Mixed Test (6 URLs - Multiple Domains)
```
https://github.com/features
https://github.com/pricing
https://stackoverflow.com/questions
https://stackoverflow.com/tags
https://developer.mozilla.org/en-US/docs/Web/HTML
https://developer.mozilla.org/en-US/docs/Web/CSS
```

## 🚀 Progressive Cache Testing Sequence

Run these tests in order to see the cache optimization in action:

**Step 1: Initial Cache Building (0% cache expected)**
```
https://github.com/features
https://stackoverflow.com/questions
```

**Step 2: Partial Cache Hit (50% cache expected)**  
```
https://github.com/features
https://developer.mozilla.org/en-US/docs/Web/HTML
```

**Step 3: Growing Cache (100% individual cache expected)**
```
https://github.com/features
https://stackoverflow.com/questions
https://developer.mozilla.org/en-US/docs/Web/HTML
```

**Step 4: Mixed Expansion (33% cache expected)**
```
https://github.com/pricing
https://stackoverflow.com/questions
https://developer.mozilla.org/en-US/docs/Web/CSS
```

**Step 5: Complete Cache Hit (100% complete cache expected)**
```
https://github.com/features
https://stackoverflow.com/questions
https://developer.mozilla.org/en-US/docs/Web/HTML
```

💡 **Usage**: Copy and paste these URLs into your frontend URL input field to test the cache optimization system consistently without hitting random domains each time. 
