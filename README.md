# TamteKlipy

Prywatna platforma do zarządzania klipami z gier i zrzutami ekranu. Stworzona tylko dla znajomych.

## Tech Stack:

**Backend:**

- Python 3.11+ z FastAPI
- SQLite + SQLAlchemy
- Uwierzytelnianie JWT z bcrypt
- Alembic do migracji

**Frontend:**

- React + Vite
- Tailwind CSS
- React Router
- Axios

**Wdrożenie:**

- Raspberry Pi Zero 2 W
- Dysk USB 64GB (ext4)
- Cloudflare Tunnel (HTTPS)
- Usługi systemd

## Struktura projektu

```
tamteklipy/
├── backend/
│   ├── app/
│   │   ├── routers/      # Endpointy API
│   │   ├── models/       # Modele SQLAlchemy
│   │   ├── schemas/      # Schematy Pydantic
│   │   ├── services/     # Logika biznesowa
│   │   └── core/         # Konfiguracja, auth, utils
│   ├── alembic/          # Migracje bazy danych
│   ├── tests/            # Testy
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── contexts/
│   │   └── services/
│   └── public/
├── docs/                 # Dokumentacja
└── scripts/              # Skrypty pomocnicze
```

## Konfiguracja (rozwój na Windows)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Struktura plików (na RPi)
```
/mnt/tamteklipy/
├── clips/ # Klipy wideo
├── screenshots/ # Zrzuty ekranu
├── thumbnails/ # Generowane miniatury
└── metadata/ # Pliki metadanych
```
## Funkcje MVP (Cel: 31.12.2025)

- Uwierzytelnianie użytkownika (JWT)
- Wgrywanie klipów/zrzutów ekranu
- Widok siatki z miniaturami
- Modalny odtwarzacz wideo
- System nagród (oparty o uprawnienia)

## Bezpieczeństwo

- Hasła: hashowanie bcrypt
- Auth: tokeny JWT z TTL
- Autoryzacja: uprawnienia oparte o zakresy
- Transport: HTTPS przez Cloudflare Tunnel
- Limitowanie zapytań i walidacja danych wejściowych

## Licencja

Projekt prywatny – Wszelkie prawa zastrzeżone
