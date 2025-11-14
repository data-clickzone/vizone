# IVIzone API - Vercel Deployment

Bu API, Google Sheets verilerinizi CORS sorunu olmadan çeker.

## 📦 Dosyalar

```
vercel-api/
├── api/
│   └── index.py          # Python serverless function
├── vercel.json           # Vercel konfigürasyonu
└── README.md            # Bu dosya
```

## 🚀 Deployment Adımları

### 1. GitHub Repository Oluşturun

1. GitHub'a gidin: https://github.com
2. Sağ üst köşede **"+"** → **"New repository"**
3. Repository ismi: `ivizone-api`
4. **Public** seçin
5. **Create repository** tıklayın

### 2. Dosyaları GitHub'a Yükleyin

**Yöntem A: GitHub Web Interface (Kolay)**

1. Yeni oluşturduğunuz repository'de **"Add file"** → **"Upload files"**
2. Bu klasördeki TÜM dosyaları sürükle-bırak yapın:
   - `api/index.py`
   - `vercel.json`
   - `README.md`
3. **Commit changes** tıklayın

**Yöntem B: Git ile (Terminal)**

```bash
# Dosyaların olduğu klasöre gidin
cd vercel-api

# Git başlat
git init
git add .
git commit -m "Initial commit"

# GitHub'a bağla (URL'yi kendi repo'nuzla değiştirin)
git remote add origin https://github.com/KULLANICI_ADINIZ/ivizone-api.git
git branch -M main
git push -u origin main
```

### 3. Vercel'e Deploy Edin

1. **Vercel'e gidin:** https://vercel.com
2. **Sign up** (GitHub ile giriş yapın)
3. **"Add New..."** → **"Project"**
4. **Import Git Repository** → GitHub'dan `ivizone-api` seçin
5. **Deploy** tıklayın (başka ayar değiştirmeyin!)

### 4. API URL'nizi Alın

Deploy tamamlandıktan sonra:
- Vercel size bir URL verecek: `https://ivizone-api-xxx.vercel.app`
- Bu URL'yi kopyalayın!

### 5. Dashboard'u Güncelleyin

API URL'nizi bana gönderin, dashboard'u güncelleyeceğim!

## 🔧 Test Etme

API URL'nizi tarayıcıda açın, JSON veri görmelisiniz:
```
https://your-api-url.vercel.app/api
```

## ❓ Sorun Giderme

**"Build failed" hatası:**
- `vercel.json` dosyasının doğru yerde olduğundan emin olun

**"404 Not Found":**
- URL'nin sonuna `/api` eklemeyi deneyin

**Veri gelmiyor:**
- Google Sheets'in public olduğundan emin olun
