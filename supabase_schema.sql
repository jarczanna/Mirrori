-- ============================================
-- SCHEMAT BAZY DANYCH — Stylizacja MVP
-- Wklej całość w Supabase SQL Editor i uruchom
-- ============================================

-- TABELA: users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'essential' CHECK (plan IN ('essential', 'premium')),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: analyses (analiza sylwetki)
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_url TEXT,
    ankieta_json JSONB,
    ai_analysis_json JSONB,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'corrected')),
    stylistka_korekta JSONB,
    stylistka_komentarz TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: wardrobe (szafa użytkownika)
CREATE TABLE wardrobe (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    zdjecie_url TEXT,
    opis TEXT,
    kategoria TEXT CHECK (kategoria IN ('bluzka', 'spodnie', 'sukienka', 'spodnica', 'okrycie_wierzchnie', 'buty', 'akcesoria', 'inne')),
    kolor TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: style_cases (baza RAG — zweryfikowane przypadki)
CREATE TABLE style_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    typ_sylwetki TEXT NOT NULL,
    kolorystyka TEXT,
    proporcje JSONB,
    rekomendacje JSONB,
    czego_unikac JSONB,
    tagi TEXT[],
    zrodlo_analysis_id UUID REFERENCES analyses(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABELA: stylizations (stylizacje miesięczne)
CREATE TABLE stylizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    typ TEXT NOT NULL CHECK (typ IN ('internet', 'szafa', 'tygodniowa')),
    items JSONB,
    miesiac DATE,
    zatwierdzona BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEKSY
-- ============================================
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_wardrobe_user_id ON wardrobe(user_id);
CREATE INDEX idx_style_cases_tagi ON style_cases USING GIN(tagi);
CREATE INDEX idx_stylizations_user_id ON stylizations(user_id);

-- ============================================
-- FUNKCJA: auto-update updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_analyses_updated_at
    BEFORE UPDATE ON analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- STORAGE BUCKET (uruchom osobno w Supabase)
-- ============================================
-- W Supabase Dashboard → Storage → New Bucket
-- Nazwa: sylwetki
-- Public: NIE (private)
-- Nazwa: szafa
-- Public: NIE (private)
