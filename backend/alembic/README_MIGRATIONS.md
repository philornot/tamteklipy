# Alembic Migrations - TamteKlipy

## Podstawowe komendy

### Tworzenie nowej migracji

Po dodaniu/zmianie modeli SQLAlchemy:
```bash
# Automatyczne generowanie migracji na podstawie zmian w modelach
alembic revision --autogenerate -m "Opis zmian"

# Ręczne tworzenie pustej migracji
alembic revision -m "Opis zmian"
```

### Zastosowanie migracji
```bash
# Zastosuj wszystkie niezastosowane migracje
alembic upgrade head

# Zastosuj tylko jedną migrację do przodu
alembic upgrade +1

# Zastosuj do konkretnej wersji
alembic upgrade <revision_id>
```

### Cofnięcie migracji
```bash
# Cofnij ostatnią migrację
alembic downgrade -1

# Cofnij do konkretnej wersji
alembic downgrade <revision_id>

# Cofnij wszystkie migracje
alembic downgrade base
```

### Sprawdzanie statusu
```bash
# Aktualna wersja bazy
alembic current

# Historia migracji
alembic history

# Szczegóły konkretnej migracji
alembic show <revision_id>
```

## Workflow

1. **Zmiana w modelu**
   ```python
   # app/models/user.py
   class User(Base):
       # Dodajesz nowe pole
       phone_number = Column(String(20), nullable=True)
   ```

2. **Generowanie migracji**
   ```bash
   alembic revision --autogenerate -m "Add phone_number to users"
   ```

3. **Sprawdzenie wygenerowanego pliku**  
   Otwórz plik w `alembic/versions/` i sprawdź czy zmiany są poprawne.

4. **Zastosowanie migracji**
   ```bash
   alembic upgrade head
   ```

5. **Commit do git**
   ```bash
   git add alembic/versions/<new_migration>.py
   git commit -m "Migration: Add phone_number to users"
   ```

## Na produkcji (RPi)
```bash
# Pull najnowszego kodu
cd ~/tamteklipy
git pull

# Aktywuj venv
cd backend
source venv/bin/activate

# Zastosuj migracje
alembic upgrade head

# Restart serwisu
sudo systemctl restart tamteklipy-backend
```

## Dobre praktyki

- Zawsze sprawdzaj wygenerowane migracje przed zastosowaniem  
- Nigdy nie edytuj zastosowanych migracji - twórz nowe  
- Backup bazy przed zastosowaniem migracji na produkcji  
- Testuj migracje na developmencie przed produkcją  
- Commituj migracje razem ze zmianami w modelach  

## Troubleshooting

### Konflikt migracji
```bash
# Sprawdź historię
alembic history

# Jeśli są konflikty, stwórz merge migration
alembic merge heads -m "Merge migrations"
```

### Reset bazy (development only!)
```bash
# Usuń bazę
rm tamteklipy.db

# Zastosuj wszystkie migracje od początku
alembic upgrade head
```

### Alembic nie wykrywa zmian
- Upewnij się że modele są importowane w `alembic/env.py`  
- Sprawdź czy `Base.metadata` jest poprawnie ustawione  
- Usuń `__pycache__` i spróbuj ponownie  
