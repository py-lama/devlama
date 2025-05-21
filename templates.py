# -*- coding: utf-8 -*-
"""
Szablony do generowania kodu Python przez modele LLM.

Ten moduł zawiera szablony zapytań, które pomagają w generowaniu
lepszego i bardziej niezawodnego kodu Python przez modele językowe.
"""

# Podstawowy szablon do generowania kodu Python
BASIC_CODE_TEMPLATE = """
Wygeneruj działający kod Python, który {task}.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Używać standardowych bibliotek Python tam, gdzie to możliwe
4. Zawierać komentarze wyjaśniające kluczowe elementy
5. Obsługiwać podstawowe przypadki błędów

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon z uwzględnieniem platformy
PLATFORM_AWARE_TEMPLATE = """
Wygeneruj działający kod Python, który {task}.

Kod będzie uruchamiany na platformie: {platform} (system operacyjny: {os}).

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Używać bibliotek kompatybilnych z {platform}
4. Zawierać komentarze wyjaśniające kluczowe elementy
5. Obsługiwać podstawowe przypadki błędów
6. Unikać używania funkcji specyficznych dla innych systemów operacyjnych

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do generowania kodu z określonymi zależnościami
DEPENDENCY_AWARE_TEMPLATE = """
Wygeneruj działający kod Python, który {task}.

Możesz używać TYLKO następujących bibliotek zewnętrznych: {dependencies}.
Jeśli potrzebujesz innych funkcji, zaimplementuj je samodzielnie.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy (tylko z dozwolonych bibliotek)
3. Zawierać komentarze wyjaśniające kluczowe elementy
4. Obsługiwać podstawowe przypadki błędów

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do debugowania istniejącego kodu
DEBUG_CODE_TEMPLATE = """
Poniższy kod Python zawiera błąd:

```python
{code}
```

Błąd:
{error_message}

Napraw ten kod, aby działał prawidłowo. Upewnij się, że:
1. Wszystkie importy są poprawne
2. Składnia jest prawidłowa
3. Logika działa zgodnie z zamierzeniem
4. Kod obsługuje przypadki brzegowe i potencjalne błędy

Zwróć tylko poprawiony kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do generowania kodu z testami jednostkowymi
TESTABLE_CODE_TEMPLATE = """
Wygeneruj działający kod Python, który {task}.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Być zorganizowany w funkcje lub klasy z jasno określonymi odpowiedzialnościami
4. Zawierać komentarze wyjaśniające kluczowe elementy
5. Obsługiwać podstawowe przypadki błędów

Dodatkowo, dołącz testy jednostkowe, które sprawdzają poprawność działania kodu.

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do generowania kodu z uwzględnieniem bezpieczeństwa
SECURE_CODE_TEMPLATE = """
Wygeneruj bezpieczny kod Python, który {task}.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Implementować najlepsze praktyki bezpieczeństwa
4. Walidować dane wejściowe
5. Obsługiwać wyjątki w bezpieczny sposób
6. Unikać typowych podatności (np. wstrzykiwanie kodu, niekontrolowane dostępy do plików)
7. Zawierać komentarze wyjaśniające aspekty bezpieczeństwa

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do generowania kodu z uwzględnieniem wydajności
PERFORMANCE_CODE_TEMPLATE = """
Wygeneruj wydajny kod Python, który {task}.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Być zoptymalizowany pod kątem wydajności
4. Unikać niepotrzebnych operacji i nadmiernego zużycia pamięci
5. Wykorzystywać odpowiednie struktury danych i algorytmy
6. Zawierać komentarze wyjaśniające wybory dotyczące wydajności

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Szablon do generowania kodu zgodnego z PEP 8
PEP8_CODE_TEMPLATE = """
Wygeneruj kod Python zgodny z PEP 8, który {task}.

Twój kod powinien:
1. Być kompletny i gotowy do uruchomienia
2. Zawierać wszystkie niezbędne importy
3. Ściśle przestrzegać konwencji PEP 8 (nazewnictwo, wcięcia, długość linii, itp.)
4. Zawierać docstringi zgodne z PEP 257
5. Obsługiwać podstawowe przypadki błędów

Zwróć tylko kod Python w bloku kodu Markdown: ```python ... ```
"""

# Funkcja do wyboru odpowiedniego szablonu na podstawie kontekstu zapytania
def get_template(task: str, template_type: str = "basic", **kwargs) -> str:
    """
    Wybiera i wypełnia odpowiedni szablon na podstawie typu i parametrów.
    
    Args:
        task: Opis zadania do wykonania przez kod
        template_type: Typ szablonu (basic, platform_aware, dependency_aware, debug, testable, secure, performance, pep8)
        **kwargs: Dodatkowe parametry specyficzne dla wybranego szablonu
    
    Returns:
        Wypełniony szablon gotowy do wysłania do modelu LLM
    """
    templates = {
        "basic": BASIC_CODE_TEMPLATE,
        "platform_aware": PLATFORM_AWARE_TEMPLATE,
        "dependency_aware": DEPENDENCY_AWARE_TEMPLATE,
        "debug": DEBUG_CODE_TEMPLATE,
        "testable": TESTABLE_CODE_TEMPLATE,
        "secure": SECURE_CODE_TEMPLATE,
        "performance": PERFORMANCE_CODE_TEMPLATE,
        "pep8": PEP8_CODE_TEMPLATE
    }
    
    template = templates.get(template_type.lower(), BASIC_CODE_TEMPLATE)
    
    # Wypełnij szablon podstawowymi parametrami
    prompt = template.format(task=task, **kwargs)
    
    return prompt
