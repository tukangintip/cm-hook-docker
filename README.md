# webhook-chatmatter

Layanan webhook ringan yang menerima payload dari ChatMatter (tanpa autentikasi)
dan meneruskan isinya ke grup Telegram sebagai pesan teks / foto.

## Cara kerja

```
POST /webhook  (JSON, no auth)
        |
        v
  format pesan
        |
        v
  Telegram Bot API
   - sendPhoto  jika field "file" berupa URL gambar
   - sendMessage jika hanya teks, atau file video/audio/lainnya
                 (URL lampiran disertakan di teks)
```

## Konfigurasi

Semua kredensial dibaca dari file `.env` (lihat `.env.example`):

| Variabel             | Keterangan                                  |
| -------------------- | ------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Token bot dari @BotFather                   |
| `TELEGRAM_CHAT_ID`   | ID grup tujuan (mis. `-1001234567890`)      |
| `WEBHOOK_PORT`       | Port HTTP tempat service mendengarkan (default `9091`) |

## Menjalankan dengan Docker

```bash
cp .env.example .env     # lalu isi token & chat id
docker compose up -d --build
```

Cek status:

```bash
docker compose ps
curl http://localhost:9091/health   # -> {"status":"ok"}
```

Log:

```bash
docker compose logs -f webhook-chatmatter
```

## Menguji webhook

Kirim payload sesuai `example-webhook-payload.json`:

```bash
curl -X POST http://localhost:9091/webhook \
  -H "Content-Type: application/json" \
  -d @example-webhook-payload.json
```

Response sukses:

```json
{ "status": "sent", "message_id": 123 }
```

## Format payload yang dikenali

```json
{
  "messageId": "...",
  "fromMe": false,
  "from": "628xxxxxxxxx",
  "lid": "xxxxxxxxxxxxxxx",
  "to": "966xxxxxxxxx",
  "timestamp": 1783167575,
  "datetimes": "2026-07-04 12:19:36",
  "message": "Gggga",
  "file": "https://.../image.jpg"
}
```

- Jika `file` berakhir dengan `.jpg/.jpeg/.png/.webp/.gif` -> dikirim sebagai **foto** (dengan caption).
- Jika `file` berupa **video** (`.mp4/.mov/.m4v/.webm/.mkv/.avi/.3gp/.wmv/.flv/.ts`) atau
  **audio** (`.mp3/.m4a/.aac/.ogg/.oga/.opus/.wav/.flac/.wma`) -> URL lampiran disertakan
  di **pesan teks** (tidak di-upload sebagai media, agar andal terhadap batas ukuran Telegram).
- File tipe lain -> URL lampiran disertakan di pesan teks.
- Jika `message` dan `file` keduanya kosong -> diabaikan (respons tetap `200`).

## Logging

Log ditulis ke **stdout** (format *plain text*), ditangkap lewat Docker:

```bash
docker compose logs -f webhook-chatmatter
```

Contoh baris log:

```
2026-07-05 10:00:00 | INFO   | webhook  | IN  POST /webhook from 1.2.3.4 msgId=AC755... from=628... to=966... media=video payload={...}
2026-07-05 10:00:00 | INFO   | telegram | OUT ok message_id=374 msgId=AC755...
2026-07-05 10:00:01 | ERROR  | telegram | FAIL stage=photo msgId=AC755... detail={'ok': False, ...}
```

- Setiap webhook masuk dicatat (IP pengirim, messageId, from/to, tipe media, payload).
- Sukses pengiriman ke Telegram dicatat (message_id).
- Kegagalan pengiriman dicatat dengan tahap (`photo`/`text`) dan detail error.

## Catatan perilaku

- **Tanpa autentikasi**: endpoint `/webhook` terbuka. Batasi akses jaringan di
  tingkat reverse proxy / firewall bila perlu.
- **Selalu respons 200**: kesalahan pengiriman ke Telegram dicatat di log,
  bukan dikembalikan sebagai error ke pengirim (mencegah badai retry).

## Menjalankan tanpa Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9091
```
