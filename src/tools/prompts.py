"""MCP prompts for agent workflows."""

from src.server import mcp


def _context_instructions(work_package_id: int) -> str:
    return (
        f"1. NAJPIERW wywołaj narzędzie `get_work_package_context` z "
        f"`work_package_id={work_package_id}`, aby pobrać opis, pola własne, komentarze, "
        f"załączniki, relacje i hierarchię zadania #{work_package_id}.\n"
        "2. Jeśli w kontekście jest sekcja obrazów w opisie (lub istotne załączniki-obrazy), "
        "pobierz je narzędziem `get_attachment` z podanym ID i uwzględnij ich treść.\n"
        f"3. Wywołaj `list_work_package_code_links` z `work_package_id={work_package_id}`, "
        "aby sprawdzić powiązane pull/merge requesty i pliki (źródła niedostępne pomiń).\n"
        "4. Nie zgaduj – opieraj się wyłącznie na pobranych danych; braki nazwij wprost.\n"
    )


@mcp.prompt
def plan_work_package(work_package_id: int) -> str:
    """Plan the implementation of a work package based on its full context."""
    return (
        f"Przygotuj plan realizacji zadania OpenProject #{work_package_id}.\n\n"
        "Kroki przygotowania:\n"
        f"{_context_instructions(work_package_id)}\n"
        "Następnie odpowiedz po polsku w sekcjach:\n"
        "- **Cel** – jednym-dwoma zdaniami, co ma zostać osiągnięte.\n"
        "- **Kroki implementacji** – numerowana lista małych, weryfikowalnych kroków "
        "(uwzględnij istniejący kod z powiązanych PR/MR).\n"
        "- **Pytania otwarte** – niejasności do wyjaśnienia z PO/zgłaszającym.\n"
        "- **Ryzyka** – techniczne i biznesowe, z propozycją ograniczenia.\n"
        "- **Kryteria akceptacji** – sprawdzalne warunki ukończenia zadania.\n"
    )


@mcp.prompt
def summarize_work_package(work_package_id: int) -> str:
    """Summarize a work package: goal, status, recent decisions and blockers."""
    return (
        f"Podsumuj zadanie OpenProject #{work_package_id}.\n\n"
        "Kroki przygotowania:\n"
        f"{_context_instructions(work_package_id)}\n"
        "Następnie odpowiedz po polsku, zwięźle, w sekcjach:\n"
        "- **Cel** – po co jest to zadanie.\n"
        "- **Stan** – status, przypisanie, postęp, terminy oraz stan powiązanego kodu.\n"
        "- **Ostatnie decyzje** – ustalenia z najnowszych komentarzy (z autorem i datą).\n"
        "- **Blokery** – co blokuje postęp (relacje, pytania bez odpowiedzi, braki).\n"
    )
