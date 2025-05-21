# pylama


# Uniwersalny Serwer Ollama

https://ollama.com/search?c=vision
https://ollama.com/search?o=newest

![GUI.png](GUI.png)

Kompletne, uniwersalne rozwiązanie do uruchamiania i zarządzania lokalnym serwerem modeli językowych poprzez Ollama. Działa na wszystkich dystrybucjach Linuxa oraz macOS.

## Funkcje

- 🚀 **Uniwersalność** - działa na wszystkich dystrybucjach Linux oraz macOS
- 🔄 **Automatyczna konfiguracja** - automatyczna instalacja wymaganych pakietów
- 📝 **Interfejs webowy** - do testowania modeli w przeglądarce
- ⚙️ **Łatwa konfiguracja** - przez plik .env lub parametry wiersza poleceń
- 🌐 **Proste API REST** - do integracji z aplikacjami
- 🔄 **Obsługa wielu modeli** - z możliwością łatwego przełączania
- 📊 **Zaawansowane zarządzanie parametrami** - temperatura, max_tokens, itp.

## Wymagania

- Python 3.8+ (skrypt wykryje i zainstaluje zależności)
- [Ollama](https://ollama.com/download)
- Co najmniej jeden model Ollama (np. tinyllama, llama3, qwen, phi)

## Szybki start

1. **Pobierz i utwórz skrypt:**

   ```bash
   # Zapisz skrypt jako setup.sh
   chmod +x setup.sh
   ```

2. **Uruchom z pełną konfiguracją:**

   ```bash
   ./setup.sh
   ```

   Skrypt automatycznie:
   - Sprawdzi i zainstaluje wymagane pakiety Python
   - Sprawdzi instalację Ollama
   - Pomoże w konfiguracji modeli
   - Uruchomi serwer API

3. **Lub tylko uruchom serwer (jeśli już skonfigurowany):**

   ```bash
   ./setup.sh --run
   ```

## Dostępne opcje

Skrypt oferuje kilka przydatnych opcji:

```bash
# Wyświetlenie pomocy
./setup.sh --help

# Tylko konfiguracja środowiska (bez uruchamiania)
./setup.sh --setup

# Tylko uruchomienie serwera
./setup.sh --run

# Uruchomienie na niestandardowym porcie
./setup.sh --run --port 8080

# Zarządzanie modelami Ollama
./setup.sh --models

# Sprawdzenie wymagań systemowych
./setup.sh --check
```

## Interfejs webowy

Po uruchomieniu serwera, interfejs webowy jest dostępny pod adresem:

```
http://localhost:5001
```

Interfejs pozwala na:
- Zadawanie pytań do modelu
- Zmianę parametrów generowania
- Przeglądanie dostępnych modeli

## API REST

Serwer udostępnia następujące endpointy:

### `POST /ask`

Wysyła zapytanie do modelu Ollama.

**Żądanie**:
```json
{
  "prompt": "Co to jest Python?",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Odpowiedź**:
```json
{
  "response": "Python to wysokopoziomowy, interpretowany język programowania..."
}
```

### `GET /models`

Pobiera listę dostępnych modeli Ollama.

**Odpowiedź**:
```json
{
  "models": [
    {
      "name": "tinyllama:latest",
      "size": 1640,
      "current": true
    },
    {
      "name": "llama3:latest",
      "size": 3827,
      "current": false
    }
  ]
}
```

### `POST /echo`

Proste narzędzie do testowania działania serwera.
![img.png](img.png)
**Żądanie**:
```json
{
  "message": "Test"
}
```

**Odpowiedź**:
```json
{
  "response": "Otrzymano: Test"
}
```

## Używanie z cURL

```bash
# Zapytanie do modelu
curl -X POST -H "Content-Type: application/json" \
     -d '{"prompt":"Co to jest Python?"}' \
     http://localhost:5001/ask

# Pobranie listy modeli
curl http://localhost:5001/models

# Test echo
curl -X POST -H "Content-Type: application/json" \
     -d '{"message":"Test"}' \
     http://localhost:5001/echo
```

## Plik konfiguracyjny .env

Skrypt tworzy plik `.env` z ustawieniami, które możesz edytować:

```
# Konfiguracja modelu Ollama
MODEL_NAME="tinyllama:latest"

# Konfiguracja serwera
OLLAMA_URL="http://localhost:11434"
SERVER_PORT=5001

# Parametry generowania
TEMPERATURE=0.7
MAX_TOKENS=1000
```

## Obsługiwane modele

Skrypt działa z wszystkimi modelami dostępnymi w Ollama. Oto szczegółowa lista najpopularniejszych modeli:

| Model | Rozmiar | Przeznaczenie |
|-------|---------|---------------|
| **llama3** | 8B | Ogólnego przeznaczenia, dobry do większości zadań |
| **phi3** | 3.8B | Szybki, dobry do prostszych zadań, zoptymalizowany pod kątem kodu |
| **mistral** | 7B | Ogólnego przeznaczenia, efektywny energetycznie |
| **gemma** | 7B | Dobry do zadań języka naturalnego i kreatywnego pisania |
| **tinyllama** | 1.1B | Bardzo szybki, idealny dla słabszych urządzeń |
| **qwen** | 7-14B | Dobry w analizie tekstu, wsparcie dla języków azjatyckich |
| **llava** | 7-13B | Multimodalny z obsługą obrazów - pozwala na analizę obrazów i tekstu |
| **codellama** | 7-34B | Wyspecjalizowany model do kodowania - świetny do generowania i analizy kodu |
| **vicuna** | 7-13B | Wytrenowany na konwersacjach, dobry do dialogów |
| **falcon** | 7-40B | Szybki i efektywny, dobry stosunek wydajności do rozmiaru |
| **orca-mini** | 3B | Dobry do podstawowych zadań NLP |
| **wizardcoder** | 13B | Stworzony do zadań związanych z kodem |
| **llama2** | 7-70B | Poprzednia generacja modelu Meta, sprawdzony w różnych zastosowaniach |
| **stablelm** | 3-7B | Dobry do generowania tekstu i dialogów |
| **dolphin** | 7B | Koncentruje się na naturalności dialogów |
| **neural-chat** | 7-13B | Zoptymalizowany pod kątem urządzeń Intel |
| **starling** | 7B | Mniejszy ale skuteczny, zoptymalizowany pod kątem jakości odpowiedzi |
| **openhermes** | 7B | Dobra dokładność, postępowanie zgodnie z instrukcjami |
| **yi** | 6-34B | Zaawansowany model wielojęzyczny |

### Wybór rozmiaru modelu

Przy wyborze własnego modelu, warto rozważyć różne rozmiary:

- **Mini (1-3B)**: Bardzo małe modele - szybkie, ale ograniczone możliwości
- **Small (3-7B)**: Małe modele - dobry kompromis szybkość/jakość
- **Medium (8-13B)**: Średnie modele - lepsze odpowiedzi, wymaga więcej RAM
- **Large (30-70B)**: Duże modele - najlepsza jakość, wysokie wymagania sprzętowe

### Wymagania sprzętowe

Poniżej orientacyjne wymagania sprzętowe dla różnych rozmiarów modeli:

| Rozmiar modelu | Minimalna ilość RAM | Zalecana ilość RAM | GPU |
|----------------|---------------------|-------------------|-----|
| Mini (1-3B) | 4GB | 8GB | Opcjonalnie |
| Small (3-7B) | 8GB | 16GB | Zalecany |
| Medium (8-13B) | 16GB | 24GB | Zalecany ≥4GB VRAM |
| Large (30-70B) | 32GB | 64GB | Wymagany ≥8GB VRAM |
