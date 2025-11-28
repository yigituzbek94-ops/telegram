# 🚀 IELTS Pro Bot - Render.com ga Deploy

## 📋 Kerakli fayllar (IELTS_BOT_DEPLOY papkasida)

```
IELTS_BOT_DEPLOY/
├── ielts_bot.py      ← Bot kodi
├── requirements.txt   ← Python paketlari
└── DEPLOY_RENDER.md   ← Shu fayl
```

---

## 🔧 1-QADAM: GitHub Repository Yaratish

### 1.1. GitHub.com ga kiring
- https://github.com ga o'ting
- Akkountingizga kiring (yoki ro'yxatdan o'ting)

### 1.2. Yangi Repository yarating
- "New repository" tugmasini bosing
- **Repository name:** `ielts-pro-bot`
- **Public** tanlang
- "Create repository" bosing

### 1.3. Fayllarni yuklang
- "uploading an existing file" havolasini bosing
- `IELTS_BOT_DEPLOY` papkasidagi barcha fayllarni drag-drop qiling:
  - `ielts_bot.py`
  - `requirements.txt`
- "Commit changes" bosing

---

## 🌐 2-QADAM: Render.com da Ro'yxatdan O'tish

### 2.1. Render.com ga kiring
- https://render.com ga o'ting
- "Get Started" bosing
- **GitHub bilan kiring** (eng oson)

---

## ⚙️ 3-QADAM: Background Worker Yaratish

### 3.1. Dashboard ga o'ting
- https://dashboard.render.com

### 3.2. Yangi Service yarating
- **"New +"** tugmasini bosing
- **"Background Worker"** tanlang

### 3.3. GitHub Repository ni ulang
- "Connect a repository" bosing
- `ielts-pro-bot` repository ni tanlang
- "Connect" bosing

### 3.4. Sozlamalar

| Maydon | Qiymat |
|--------|--------|
| **Name** | `ielts-pro-bot` |
| **Region** | Frankfurt (EU) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python ielts_bot.py` |
| **Instance Type** | `Free` |

### 3.5. Environment Variables qo'shish
"Environment" bo'limida quyidagilarni qo'shing:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `8527617894:AAEP1UlgDy55gogspemMYKW7RUReXp7Y2NE` |
| `OPENAI_API_KEY` | `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` |
| `GEMINI_API_KEY` | `AIzaSyC7zcMNz5IbTsuIc9DqwCiucEe43El0RXQ` |
| `ADMIN_IDS` | `8166257074` |

### 3.6. Deploy boshlash
- "Create Background Worker" bosing
- Deploy jarayoni boshlanadi (3-5 daqiqa)

---

## ✅ 4-QADAM: Tekshirish

### 4.1. Loglarni ko'ring
- Render dashboard da "Logs" tabini oching
- "Bot ishga tushdi" xabarini kuting

### 4.2. Telegram da tekshiring
- @IELTSPro95_Bot ga o'ting
- `/start` yuboring
- Bot javob berishi kerak!

---

## 🔄 Yangilash

Bot kodini yangilash uchun:
1. GitHub da faylni tahrirlang
2. Render avtomatik qayta deploy qiladi

---

## ❓ Muammolar

### Bot ishlamayapti
1. Render Logs ni tekshiring
2. Environment variables to'g'ri kiritilganmi?
3. `requirements.txt` faylida xatolik yo'qmi?

### "No module named" xatosi
- `requirements.txt` da paket qo'shilganmi?

### Token xatosi
- BOT_TOKEN to'g'ri nusxalanganmi?
- Qo'shimcha bo'sh joy yo'qmi?

---

## 📞 Yordam

Telegram: @IELTSPro95_Bot

---

**✨ Bot 24/7 ishlaydi!**

