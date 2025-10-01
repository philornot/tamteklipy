# TamteKlipy

TamteKlipy to prywatna platforma webowa do zarządzania klipami z gier oraz zrzutami ekranu, przeznaczona wyłącznie dla zamkniętej grupy znajomych. Projekt powstał z potrzeby wygodnego przechowywania, przeglądania i dzielenia się własnymi nagraniami z gier oraz screenshotami, bez konieczności korzystania z publicznych serwisów.

## Najważniejsze funkcje

- **Bezpieczne uwierzytelnianie** – logowanie z użyciem JWT, hasła hashowane bcryptem.
- **Wgrywanie i przechowywanie klipów oraz screenshotów** – pliki przechowywane lokalnie na serwerze.
- **Automatyczne generowanie miniatur** – szybki podgląd zawartości.
- **Przeglądanie w formie siatki** – wygodny widok galerii z miniaturami.
- **Odtwarzacz wideo w modalu** – szybkie oglądanie klipów bez opuszczania strony.
- **System nagród** – uprawnienia i dostęp do dodatkowych funkcji dla aktywnych użytkowników.
- **Prywatność** – dostęp tylko dla zaproszonych osób, brak indeksowania przez wyszukiwarki.

## Dla kogo?
Projekt skierowany jest do osób, które chcą mieć własne, prywatne archiwum klipów i zrzutów ekranu z gier, bez reklam, algorytmów i ryzyka utraty danych na zewnętrznych platformach. Idealny do wspólnego dzielenia się najlepszymi momentami z gier w gronie znajomych.

## Jak uruchomić projekt?

### Backend (Python/FastAPI)

1. Przejdź do katalogu backend:
   ```bash
   cd backend
   ```
2. Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
4. Uruchom serwer deweloperski:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend (React)

1. Przejdź do katalogu frontend:
   ```bash
   cd frontend
   ```
2. Zainstaluj zależności:
   ```bash
   npm install
   ```
3. Uruchom aplikację:
   ```bash
   npm run dev
   ```

## Wymagania sprzętowe i wdrożenie
- Projekt działa na Raspberry Pi Zero 2 W z dyskiem USB (ext4).
- Dostęp przez HTTPS zapewnia Cloudflare Tunnel.
- Usługi uruchamiane jako systemd.

## Bezpieczeństwo
- Hasła: hashowanie bcrypt
- Autoryzacja: tokeny JWT z TTL i uprawnieniami
- Transport: HTTPS
- Walidacja danych wejściowych i limitowanie zapytań

## Licencja
Projekt prywatny – Wszelkie prawa zastrzeżone
