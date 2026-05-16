# Stylizacja MVP

Aplikacja do stylizacji modowej z weryfikacją przez stylistkę.

## Stack
- Streamlit (frontend)
- OpenAI gpt-4o-mini (analiza multimodalna)
- Supabase (baza danych + storage)

## Uruchomienie

### 1. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2. Skonfiguruj zmienne środowiskowe
```bash
cp .env.example .env
# uzupełnij .env swoimi kluczami
```

### 3. Utwórz bazę danych w Supabase
- Otwórz Supabase Dashboard → SQL Editor
- Wklej i uruchom całość z pliku `supabase_schema.sql`
- Utwórz dwa buckety w Storage: `sylwetki` i `szafa` (oba private)

### 4. Uruchom aplikację
```bash
streamlit run app.py
```

## Struktura
```
app.py                     # strona główna z wyborem roli
pages/
  1_user.py                # flow użytkownika
  2_stylistka.py           # panel stylistki (chroniony hasłem)
services/
  supabase_service.py      # CRUD baza danych
  openai_service.py        # analiza AI + tool calling
prompts/
  analiza_sylwetki.txt     # prompt do analizy zdjęcia
supabase_schema.sql        # schemat bazy danych
requirements.txt
```

## Flow użytkownika
1. Rejestracja emailem + wybór planu
2. Ankieta (styl życia, preferencje, budżet)
3. Upload zdjęcia sylwetki
4. AI generuje analizę JSON
5. Stylistka weryfikuje w swoim panelu
6. User widzi wynik z pieczęcią "zatwierdzone przez stylistkę"

## Panel stylistki
Dostępny pod `/2_stylistka` po podaniu hasła z `.env`.
Stylistka widzi: zdjęcie + analiza AI + ankieta → może zatwierdzić lub poprawić.
