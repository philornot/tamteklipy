# TamteKlipy - Dokumentacja API

## Przegląd

RESTful API dla platformy do zarządzania klipami z gier. Wszystkie endpointy wymagają autoryzacji JWT (oprócz PUBLIC).

**Base URL**: `https://tamteklipy.com/api`  
**Autoryzacja**: `Authorization: Bearer <token>`

---

## Autoryzacja (`/api/auth`)

### POST `/auth/login`

Logowanie użytkownika.

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

**Errors**: 401 (nieprawidłowe dane/konto nieaktywne)

---

### POST `/auth/register`

Rejestracja nowego użytkownika. Tworzy automatycznie nagrodę imienną.

**Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "is_active": true,
  "award_scopes": ["award:epic_clip"]
}
```

**Response** (201): UserResponse

**Errors**: 409 (username/email już istnieje)

---

### GET `/auth/me`

Zwraca dane zalogowanego użytkownika.

**Response** (200):
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "full_name": "Jan Kowalski",
  "is_active": true,
  "is_admin": false,
  "award_scopes": ["award:epic_clip"]
}
```

---

### PATCH `/auth/me`

Aktualizacja profilu użytkownika.

**Body**:
```json
{
  "full_name": "Nowa nazwa",
  "email": "nowy@email.pl",
  "password": "NoweHaslo123!"
}
```

**Response** (200): UserResponse

**Errors**: 409 (email zajęty)

---

## Pliki (`/api/files`)

### POST `/files/upload`

Upload klipa lub screenshota (standard, do 500MB).

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
  "webp_generated": true,
  "duration": 45.2,
  "resolution": "1920x1080"
}
```

**Errors**: 422 (nieprawidłowy typ/rozmiar), 500 (storage/baza)

---

### GET `/files/upload-status/{upload_id}`

Status chunked uploadu.

**Response** (200):
```json
{
  "upload_id": "uuid",
  "chunks_received": 5,
  "total_chunks": 10,
  "complete": false,
  "clip_id": null
}
```

---

### DELETE `/files/upload-chunk/{upload_id}`

Anuluj chunked upload.

**Response** (200):
```json
{
  "message": "Upload cancelled",
  "upload_id": "uuid"
}
```

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
      "has_webp_thumbnail": true,
      "award_icons": [
        {
          "award_name": "award:epic_clip",
          "icon_url": "/api/admin/award-types/1/icon",
          "icon": "🔥",
          "lucide_icon": "flame",
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

**Headers**: `Link` (HTTP/2 Server Push dla thumbnails)

---

### GET `/files/clips/{clip_id}`

Szczegóły klipa z nagrodami.

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
  "has_webp_thumbnail": true,
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
  "thumbnail_webp_url": "/api/files/thumbnails/1",
  "download_url": "/api/files/download/1"
}
```

---

### GET `/files/download/{clip_id}`

Pobierz plik klipa.

**Response**: Plik z `Content-Disposition: attachment`

**Errors**: 404, 403, 500

---

### POST `/files/download-bulk`

Pobierz wiele plików jako ZIP (max 50, max 1GB).

**Body**:
```json
{
  "clip_ids": [1, 2, 3, 4, 5]
}
```

**Response**: ZIP `tamteklipy_YYYYMMDD_HHMMSS.zip`

**Errors**: 422 (za dużo/za duże), 404

---

### POST `/files/clips/bulk-action`

Masowa operacja na klipach (max 100).

**Body**:
```json
{
  "clip_ids": [1, 2, 3],
  "action": "delete",
  "tags": [],
  "session_name": ""
}
```

**Actions**:
- `delete`: soft delete (właściciel/admin)
- `add-tags`: TODO
- `add-to-session`: TODO

**Response** (200):
```json
{
  "success": true,
  "action": "delete",
  "processed": 3,
  "failed": 0,
  "message": "Usunięto 3 klipów",
  "details": {
    "errors": null,
    "total_requested": 3
  }
}
```

---

### GET `/files/thumbnails/{clip_id}` (PUBLIC)

Pobierz miniaturę (WebP preferred, JPEG fallback).

**Headers**: `Accept: image/webp`

**Response**: JPEG/WebP

---

### GET `/files/stream/{clip_id}` (PUBLIC)

Stream video z Range requests.

**Headers**: `Range: bytes=0-1023`

**Response**: 200 (full) / 206 (partial).

---

## Nagrody (`/api/awards`)

### GET `/awards/my-awards`

Nagrody które użytkownik może przyznawać.

**Response** (200):
```json
{
  "available_awards": [
    {
      "award_name": "award:epic_clip",
      "display_name": "Epic Clip",
      "description": "Za epicki moment",
      "icon": "🔥",
      "icon_url": "/api/admin/award-types/1/icon"
    }
  ]
}
```

---

### POST `/awards/clips/{clip_id}`

Przyznaj nagrodę.

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
  "award_display_name": "Epic Clip",
  "award_icon": "🔥",
  "awarded_at": "2025-10-05T15:30:00"
}
```

**Errors**: 404, 403 (brak uprawnień), 409 (duplikat)

---

### DELETE `/awards/clips/{clip_id}/awards/{award_id}`

Usuń nagrodę (tylko własną lub admin).

**Response** (204)

**Errors**: 404, 403

---

### GET `/awards/clips/{clip_id}`

Lista nagród dla klipa.

**Response** (200):
```json
{
  "clip_id": 42,
  "total_awards": 5,
  "awards": [...],
  "awards_by_type": {
    "award:epic_clip": 3,
    "award:funny": 2
  }
}
```

---

### GET `/awards/user/{username}`

Nagrody przyznane przez użytkownika.

**Query**: `page`, `limit`, `sort_by`, `sort_order`

**Response** (200): Paginowana lista nagród

---

### GET `/awards/leaderboard`

Ranking klipów według nagród.

**Query**: `limit` (default: 10)

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

Statystyki nagród.

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
  "most_active_users": [...],
  "top_clips_by_awards": [...],
  "current_user_breakdown": {
    "award:epic_clip": 10
  }
}
```

---

## Custom Nagrody (`/api/my-awards`)

### GET `/my-awards/my-award-types`

Lista własnych custom nagród.

**Response** (200): Lista AwardType

---

### POST `/my-awards/my-award-types`

Utwórz własną nagrodę (max 5).

**Body**:
```json
{
  "display_name": "Moja Nagroda",
  "description": "Opis",
  "color": "#FF6B9D"
}
```

**Response** (201): AwardType

**Errors**: 422 (limit 5), 409 (duplikat)

---

### DELETE `/my-awards/my-award-types/{award_type_id}`

Usuń własną nagrodę (soft delete jeśli używana).

**Response** (204)

**Note**: Blokada dla `is_personal` nagród

---

## Komentarze (`/api`)

### POST `/clips/{clip_id}/comments`

Dodaj komentarz.

**Body**:
```json
{
  "content": "Świetny klip @konrad!",
  "timestamp": 83,
  "parent_id": null
}
```

**Response** (200):
```json
{
  "id": 1,
  "clip_id": 1,
  "user_id": 1,
  "content": "Świetny klip @konrad!",
  "content_html": "Świetny klip <a href=\"/profile/konrad\" class=\"mention\">@konrad</a>!",
  "mentioned_users": ["konrad"],
  "timestamp": 83,
  "parent_id": null,
  "created_at": "2025-10-05T14:30:00",
  "edited_at": null,
  "is_deleted": false,
  "is_edited": false,
  "can_edit": true,
  "reply_count": 0,
  "user": {
    "id": 1,
    "username": "user",
    "full_name": "Jan Kowalski",
    "is_admin": false
  }
}
```

**Errors**: 404 (klip), 422 (timestamp dla screenshot/max depth)

---

### GET `/clips/{clip_id}/comments`

Lista komentarzy z replies.

**Query**: `page`, `limit` (max 100)

**Response** (200):
```json
{
  "comments": [
    {
      ...komentarz z replies...
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

---

### PUT `/comments/{comment_id}`

Edytuj komentarz (5 min od utworzenia).

**Body**:
```json
{
  "content": "Zaktualizowana treść"
}
```

**Response** (200): CommentResponse

**Errors**: 404, 403, 422 (edit window)

---

### DELETE `/comments/{comment_id}`

Usuń komentarz (soft delete, właściciel/admin).

**Response** (200):
```json
{
  "message": "Komentarz został usunięty"
}
```

---

### GET `/users/mentions`

Sugestie użytkowników do @mention.

**Query**: `query` (min 2 chars), `limit` (default: 5)

**Response** (200):
```json
[
  {
    "username": "konrad",
    "full_name": "Konrad Kowalski",
    "user_id": 2
  }
]
```

---

## Admin (`/api/admin`)

### GET `/admin/award-types`

Lista wszystkich typów nagród.

**Response** (200): Lista AwardType

---

### GET `/admin/award-types/detailed`

Szczegółowe info o typach nagród z uprawnieniami.

**Response** (200):
```json
[
  {
    "id": 1,
    "name": "award:epic_clip",
    "display_name": "Epic Clip",
    "description": "...",
    "icon": "🔥",
    "lucide_icon": "flame",
    "color": "#FF6B9D",
    "icon_type": "custom|lucide|emoji",
    "icon_url": "/api/admin/award-types/1/icon",
    "is_system_award": true,
    "is_personal": false,
    "created_by_user_id": null,
    "created_by_username": null,
    "can_edit": false,
    "can_delete": false,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST `/admin/award-types`

Utwórz systemowy typ nagrody (admin only).

**Body**: AwardTypeCreate

**Response** (201): AwardType

**Errors**: 409 (duplikat)

---

### PATCH `/admin/award-types/{award_type_id}`

Aktualizuj typ nagrody (admin/twórca).

**Body**:
```json
{
  "display_name": "Nowa nazwa",
  "description": "...",
  "icon": "🔥",
  "lucide_icon": "flame",
  "color": "#FF6B9D",
  "is_personal": false
}
```

**Response** (200): AwardType z icon_type i icon_url

**Errors**: 404, 403

**Note**: `is_personal` tylko admin, nie dla system awards

---

### POST `/admin/award-types/{award_type_id}/icon`

Upload ikony (PNG/JPG/WebP, max 500KB).

**Body**: multipart/form-data z `file`

**Response** (200):
```json
{
  "message": "Ikona uploaded",
  "icon_url": "/api/admin/award-types/1/icon",
  "filename": "award_1_20250101_120000.png"
}
```

**Errors**: 404, 403, 422 (typ/rozmiar)

**Note**: Wyczyść `lucide_icon` przy uploadzie custom

---

### GET `/admin/award-types/{award_type_id}/icon`

Pobierz ikonę.

**Response**: PNG/JPG/WebP

---

### DELETE `/admin/award-types/{award_type_id}`

Usuń typ nagrody (jeśli nieużywany).

**Response** (200):
```json
{
  "message": "Typ nagrody został usunięty",
  "award_type_id": 1,
  "name": "award:custom"
}
```

**Errors**: 404, 403, 422 (is_system/is_personal/używany)

**Note**: Usuwa też plik ikony

---

### GET `/admin/users`

Lista użytkowników (admin only).

**Response** (200): Lista User

---

### POST `/admin/users`

Utwórz użytkownika bez hasła (admin only). Tworzy nagrodę imienną.

**Body**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "full_name": "Jan Kowalski",
  "is_admin": false
}
```

**Response** (201):
```json
{
  "id": 5,
  "username": "newuser",
  "email": "user@example.com",
  "full_name": "Jan Kowalski",
  "is_active": true,
  "is_admin": false,
  "message": "Użytkownik utworzony bez hasła - może je ustawić w profilu"
}
```

**Errors**: 409 (username/email)

---

### PATCH `/admin/users/{user_id}`

Aktualizuj użytkownika (admin only).

**Body**:
```json
{
  "username": "newname",
  "email": "new@email.com",
  "full_name": "Nowa Nazwa",
  "is_active": true,
  "is_admin": false
}
```

**Response** (200): User

**Errors**: 404, 409 (duplikat)

---

### DELETE `/admin/users/{user_id}`

Usuń użytkownika (admin only). Usuwa też nagrodę imienną.

**Response** (200):
```json
{
  "message": "Użytkownik został usunięty (wraz z nagrodą imienną)",
  "user_id": 5,
  "username": "user"
}
```

**Errors**: 404, 422 (blokada własne konto/ma klipy)

---

### PATCH `/admin/users/{user_id}/deactivate`

Dezaktywuj użytkownika (admin only).

**Response** (200)

**Errors**: 400 (własne konto/już nieaktywny)

---

### PATCH `/admin/users/{user_id}/activate`

Aktywuj użytkownika (admin only).

**Response** (200)

---

### DELETE `/admin/clips/{clip_id}`

Usuń klip (soft delete, admin only).

**Response** (200):
```json
{
  "message": "Klip został usunięty",
  "clip_id": 1,
  "filename": "epic.mp4"
}
```

---

### GET `/admin/clips/{clip_id}/restore`

Przywróć klip (admin only).

**Response** (200):
```json
{
  "message": "Klip został przywrócony",
  "clip_id": 1,
  "filename": "epic.mp4"
}
```

---

### GET `/admin/awards`

Lista wszystkich nagród z filtrami (admin only).

**Query**: `page`, `limit`, `sort_by`, `sort_order`, `user_id`, `clip_id`, `award_name`

**Response** (200): Paginowana lista nagród z join do clips/users

---

### PATCH `/admin/awards/{award_id}`

Aktualizuj nagrodę (admin only).

**Body**:
```json
{
  "award_name": "award:other",
  "clip_id": 99
}
```

**Response** (200): Award

**Errors**: 404, 422 (nieznany typ/klip)

---

### DELETE `/admin/awards/{award_id}`

Usuń nagrodę (admin only).

**Response** (200):
```json
{
  "message": "Nagroda została usunięta",
  "award_id": 1
}
```

---

## Kody błędów

| Kod | Znaczenie |
|-----|-----------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict (duplikat) |
| 422 | Unprocessable Entity (walidacja) |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

**Format błędu**:
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

---

## Uwagi techniczne

- **Storage**: `/home/filip/tamteklipy_storage` (prod) / `./uploads` (dev)
- **Thumbnails**: JPEG (fallback) + WebP (primary), generowane przez FFmpeg
- **Chunked upload**: 5MB chunks, SHA256 verification
- **Rate limiting**: TODO
- **WebSockets**: TODO (dla live notifications)