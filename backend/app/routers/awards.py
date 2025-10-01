"""
Router dla systemu nagród - przyznawanie i zarządzanie nagrodami
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/types")
async def get_award_types():
    """
    Pobierz wszystkie typy nagród dostępne w systemie
    GET /api/awards/types
    """
    # TODO: Implementacja po dodaniu bazy danych
    # 1. Pobierz wszystkie AwardTypes z bazy
    # 2. Zwróć listę z nazwami, ikonami, opisami

    return {
        "award_types": [],
        "total": 0,
        "message": "Implementacja wkrótce"
    }


@router.get("/my-awards")
async def get_my_awards():
    """
    Pobierz nagrody które aktualny użytkownik może przyznawać
    GET /api/awards/my-awards
    Wymaga: Authorization header
    """
    # TODO: Implementacja po dodaniu JWT i bazy
    # 1. Pobierz user_id z tokenu
    # 2. Pobierz przypisane nagrody użytkownika (z JWT scope)
    # 3. Zwróć listę dostępnych nagród

    return {
        "my_awards": [],
        "message": "Implementacja wkrótce (wymaga JWT)"
    }


@router.post("/clips/{clip_id}/award")
async def give_award_to_clip(clip_id: int, award_type_id: int):
    """
    Przyznaj nagrodę do klipa
    POST /api/awards/clips/{clip_id}/award
    Body: { "award_type_id": 1 }
    Wymaga: Authorization header
    """
    # TODO: Implementacja po dodaniu bazy i JWT
    # 1. Pobierz user_id z tokenu
    # 2. Sprawdź czy użytkownik ma uprawnienia do tej nagrody (scope)
    # 3. Sprawdź czy klip istnieje
    # 4. Sprawdź czy użytkownik już nie przyznał tej nagrody
    # 5. Zapisz nagrodę w bazie
    # 6. Zwróć potwierdzenie

    return {
        "message": "Award endpoint - implementacja wkrótce",
        "clip_id": clip_id,
        "award_type_id": award_type_id,
        "status": "not_implemented"
    }


@router.delete("/clips/{clip_id}/award/{award_id}")
async def remove_award_from_clip(clip_id: int, award_id: int):
    """
    Usuń nagrodę z klipa (tylko własną)
    DELETE /api/awards/clips/{clip_id}/award/{award_id}
    Wymaga: Authorization header
    """
    # TODO: Implementacja po dodaniu bazy i JWT
    # 1. Pobierz user_id z tokenu
    # 2. Sprawdź czy nagroda należy do użytkownika
    # 3. Usuń nagrodę z bazy

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Usuwanie nagród będzie dostępne wkrótce"
    )


@router.get("/clips/{clip_id}/awards")
async def get_clip_awards(clip_id: int):
    """
    Pobierz wszystkie nagrody przyznane do klipa
    GET /api/awards/clips/{clip_id}/awards
    """
    # TODO: Implementacja po dodaniu bazy
    # 1. Sprawdź czy klip istnieje
    # 2. Pobierz wszystkie nagrody dla tego klipa
    # 3. Pogrupuj po typach nagród
    # 4. Zwróć listę z info kto przyznał

    return {
        "clip_id": clip_id,
        "awards": [],
        "total_awards": 0,
        "message": "Implementacja wkrótce"
    }


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Ranking klipów według liczby nagród
    GET /api/awards/leaderboard?limit=10
    """
    # TODO: Implementacja po dodaniu bazy
    # 1. Pobierz klipy z największą liczbą nagród
    # 2. Posortuj po popularności
    # 3. Zwróć top N klipów

    return {
        "leaderboard": [],
        "limit": limit,
        "message": "Leaderboard - implementacja wkrótce"
    }


@router.get("/stats")
async def get_award_stats():
    """
    Statystyki nagród w systemie
    GET /api/awards/stats
    """
    # TODO: Implementacja po dodaniu bazy
    # 1. Liczba wszystkich przyznanych nagród
    # 2. Najpopularniejsze typy nagród
    # 3. Najbardziej aktywni użytkownicy (przyznający nagrody)

    return {
        "total_awards": 0,
        "most_popular_award": None,
        "most_active_users": [],
        "message": "Statystyki - implementacja wkrótce"
    }
