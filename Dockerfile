FROM python:3.11-slim

WORKDIR /app

# requirements.txt ni nusxalash va kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodini nusxalash
COPY bot.py .

# APK fayllar uchun papka yaratish
RUN mkdir -p apk_files

# Botni ishga tushirish
CMD ["python", "bot.py"]
