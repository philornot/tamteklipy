# TamteKlipy - Dokumentacja API

## Przegląd

API TamteKlipy to RESTful backend dla platformy do zarządzania klipami z gier. Wszystkie endpointy wymagają autoryzacji
JWT (oprócz zaznaczonych jako PUBLIC).

**Base URL**: `https://your-domain.com/api`  
**Autoryzacja**: Bearer Token w headerze `Authorization: Bearer <token>`

---

## Autoryzacja (`/api/auth`)

### POST `/auth/login`

Logowanie użytkownika - zwraca JWT token.

**Body** (form-data):

```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200):

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Errors**: 401 (nieprawidłowe dane), 401 (konto nieaktywne)

---

### POST `/auth/register`

Rejestracja nowego użytkownika (TODO: tylko admin).

**Body**:

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "award_scopes": [
    "award:epic_clip"
  ]
}
```

**Response** (201):

```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "full_name": "Jan Kowalski",
  "is_active": true,
  "award_scopes": [
    "award:epic_clip"
  ]
}
```

**Errors**: 409 (username/email już istnieje)

---

### GET `/auth/me`

Zwraca dane aktualnie zalogowanego użytkownika.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):

```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "full_name": "Jan Kowalski",
  "is_active": true,
  "is_admin": false,
  "award_scopes": [
    "award:epic_clip",
    "award:funny"
  ]
}
```

---

## Pliki (`/api/files`)

### POST `/files/upload`

Upload klipa lub screenshota.

**Headers**: `Authorization: Bearer <token>`  
**Body**: multipart/form-data z polem `file`

**Supported formats**:

- Video: MP4, WebM, MOV (max 500MB)
- Image: PNG, JPG (max 100MB)

**Response** (200):

```json
{
  "message": "Plik został przesłany pomyślnie",
  "clip_id": 42,
  "filename": "my_clip.mp4",
  "file_size_mb": 15.3,
  "clip_type": "video",
  "uploader": "user",
  "created_at": "2025-10-05T14:30:00",
  "thumbnail_generated": true,
  "duration": 45.2,
  "resolution": "1920x1080"
}
```

**Errors**:

- 422 (nieprawidłowy typ pliku)
- 422 (plik za duży)
- 500 (błąd storage/bazy)

---

### GET `/files/clips`

Lista klipów z paginacją i filtrowaniem.

**Query params**:

- `page` (default: 1)
- `limit` (default: 50, max: 100)
- `sort_by` (created_at, filename, file_size, duration)
- `sort_order` (asc, desc)
- `clip_type` (video, screenshot)
- `uploader_id` (int)

**Response** (200):

```json
{
  "clips": [
    {
      "id": 1,
      "filename": "epic_play.mp4",
      "clip_type": "video",
      "file_size": 15728640,
      "file_size_mb": 15.0,
      "duration": 45.2,
      "width": 1920,
      "height": 1080,
      "created_at": "2025-10-05T14:30:00",
      "uploader_username": "user",
      "uploader_id": 1,
      "award_count": 3,
      "has_thumbnail": true,
      "award_icons": [
        {
          "award_name": "award:epic_clip",
          "icon_url": "/api/admin/award-types/1/icon",
          "icon": "🔥",
          "count": 2
        }
      ]
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

---

### GET `/files/clips/{clip_id}`

Szczegóły pojedynczego klipa z nagrodami.

**Response** (200):

```json
{
  "id": 1,
  "filename": "epic_play.mp4",
  "clip_type": "video",
  "file_size": 15728640,
  "file_size_mb": 15.0,
  "duration": 45.2,
  "width": 1920,
  "height": 1080,
  "created_at": "2025-10-05T14:30:00",
  "uploader_username": "user",
  "uploader_id": 1,
  "award_count": 3,
  "has_thumbnail": true,
  "awards": [
    {
      "id": 1,
      "award_name": "award:epic_clip",
      "user_id": 2,
      "username": "other_user",
      "awarded_at": "2025-10-05T15:00:00"
    }
  ],
  "thumbnail_url": "/api/files/thumbnails/1",
  "download_url": "/api/files/download/1"
}
```

**Errors**: 404 (klip nie istnieje)

---

### GET `/files/download/{clip_id}`

Pobierz plik klipa.

**Headers**: `Authorization: Bearer <token>`

**Response**: Plik z headerami `Content-Disposition: attachment`

**Errors**:

- 404 (klip nie istnieje)
- 403 (brak uprawnień)
- 500 (plik nie istnieje na dysku)

---

### POST `/files/download-bulk`

Pobierz wiele plików jako ZIP (max 50).

**Body**:

```json
{
  "clip_ids": [
    1,
    2,
    3,
    4,
    5
  ]
}
```

**Response**: Archiwum ZIP z nazwą `tamteklipy_YYYYMMDD_HHMMSS.zip`

**Errors**:

- 422 (za dużo plików - max 50)
- 422 (całkowity rozmiar > 1GB)
- 404 (brak dostępnych plików)

---

### GET `/files/thumbnails/{clip_id}` (PUBLIC)

Pobierz miniaturę klipa (bez autoryzacji).

**Response**: Obraz JPEG z cache headers

**Errors**: 404 (thumbnail nie istnieje)

---

### GET `/files/stream/{clip_id}` (PUBLIC)

Streamuj video z obsługą Range requests (bez autoryzacji).

**Headers** (optional): `Range: bytes=0-1023`

**Response**:

- 200 (cały plik)
- 206 (partial content z Range)

---

## Nagrody (`/api/awards`)

### GET `/awards/my-awards`

Pobierz nagrody które użytkownik może przyznawać.

**Response** (200):

```json
{
  "available_awards": [
    {
      "award_name": "award:epic_clip",
      "display_name": "Epic Clip",
      "description": "Za epicki moment w grze",
      "icon": "🔥",
      "icon_url": "/api/admin/award-types/1/icon"
    }
  ]
}
```

---

### POST `/awards/clips/{clip_id}`

Przyznaj nagrodę do klipa.

**Body**:

```json
{
  "award_name": "award:epic_clip"
}
```

**Response** (201):

```json
{
  "id": 1,
  "clip_id": 42,
  "user_id": 1,
  "username": "user",
  "award_name": "award:epic_clip",
  "awarded_at": "2025-10-05T15:30:00"
}
```

**Errors**:

- 404 (klip nie istnieje)
- 403 (brak uprawnień do tej nagrody)
- 409 (już przyznano tę nagrodę)

---

### DELETE `/awards/clips/{clip_id}/awards/{award_id}`

Usuń nagrodę (tylko własną).

**Response** (204): No content

**Errors**:

- 404 (nagroda nie istnieje)
- 403 (nie jesteś właścicielem)

---

### GET `/awards/clips/{clip_id}`

Lista nagród dla klipa.

**Response** (200):

```json
{
  "clip_id": 42,
  "total_awards": 5,
  "awards": [
    {
      "id": 1,
      "clip_id": 42,
      "user_id": 2,
      "username": "other_user",
      "award_name": "award:epic_clip",
      "awarded_at": "2025-10-05T15:00:00"
    }
  ],
  "awards_by_type": {
    "award:epic_clip": 3,
    "award:funny": 2
  }
}
```

---

### GET `/awards/user/{username}`

Nagrody przyznane przez użytkownika.

**Query params**: `page`, `limit`, `sort_by`, `sort_order`

**Response** (200):

```json
{
  "username": "user",
  "user_id": 1,
  "total_awards": 25,
  "page": 1,
  "limit": 20,
  "pages": 2,
  "awards": [
    ...
  ]
}
```

---

### GET `/awards/leaderboard`

Ranking klipów według nagród.

**Query params**: `limit` (default: 10)

**Response** (200):

```json
{
  "leaderboard": [
    {
      "clip_id": 42,
      "filename": "epic.mp4",
      "clip_type": "video",
      "award_count": 15
    }
  ],
  "limit": 10
}
```

---

### GET `/awards/stats`

Statystyki nagród w systemie.

**Response** (200):

```json
{
  "total_awards": 1234,
  "most_popular_award": {
    "award_name": "award:epic_clip",
    "count": 456,
    "display_name": "Epic Clip",
    "icon": "🔥"
  },
  "most_active_users": [
    ...
  ],
  "top_clips_by_awards": [
    ...
  ],
  "current_user_breakdown": {
    "award:epic_clip": 10,
    "award:funny": 5
  }
}
```

---

## Custom Nagrody (`/api/my-awards`)

### GET `/my-awards/my-award-types`

Lista własnych custom nagród.

**Response** (200):

```json
[
  {
    "id": 10,
    "name": "award:user_1_moja_nagroda",
    "display_name": "Moja Nagroda",
    "description": "Osobista nagroda",
    "icon": "🏆",
    "color": "#FF6B9D",
    "icon_url": null
  }
]
```

---

### POST `/my-awards/my-award-types`

Utwórz własną nagrodę (max 5 per user).

**Body**:

```json
{
  "display_name": "Moja Nagroda",
  "description": "Opis",
  "color": "#FF6B9D"
}
```

**Response** (201): AwardType object

**Errors**: 422 (limit 5 przekroczony)

---

### DELETE `/my-awards/my-award-types/{award_type_id}`

Usuń własną nagrodę.

**Response** (204): No content

**Note**: Soft delete jeśli była używana, hard delete jeśli nie.

---

## Admin (`/api/admin`) - tylko dla adminów

### GET `/admin/award-types`

Lista wszystkich typów nagród.

### POST `/admin/award-types`

Utwórz nowy systemowy typ nagrody.

### POST `/admin/award-types/{award_type_id}/icon`

Upload ikony dla typu nagrody.

**Body**: multipart/form-data z polem `file` (PNG/JPG/WebP, max 500KB)

### GET `/admin/award-types/{award_type_id}/icon`

Pobierz ikonę typu nagrody.

### DELETE `/admin/award-types/{award_type_id}`

Usuń typ nagrody (jeśli nieużywany).

### GET `/admin/users`

Lista wszystkich użytkowników.

### DELETE `/admin/clips/{clip_id}`

Usuń klip (soft delete).

### GET `/admin/clips/{clip_id}/restore`

Przywróć usunięty klip.

### PATCH `/admin/users/{user_id}/deactivate`

Dezaktywuj użytkownika.

### PATCH `/admin/users/{user_id}/activate`

Aktywuj użytkownika.

---

## Kody błędów

| Kod | Znaczenie                                    |
|-----|----------------------------------------------|
| 400 | Bad Request - nieprawidłowe dane             |
| 401 | Unauthorized - brak tokenu lub nieprawidłowy |
| 403 | Forbidden - brak uprawnień                   |
| 404 | Not Found - zasób nie istnieje               |
| 409 | Conflict - duplikat (już istnieje)           |
| 422 | Unprocessable Entity - błąd walidacji        |
| 429 | Too Many Requests - rate limit               |
| 500 | Internal Server Error - błąd serwera         |

---

## Format odpowiedzi błędów

```json
{
  "error": "ValidationError",
  "message": "Plik jest za duży",
  "path": "/api/files/upload",
  "details": {
    "max_size_mb": 500,
    "actual_size_mb": 750
  }
}
```
