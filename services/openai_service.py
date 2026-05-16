import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from services.supabase_service import get_similar_cases

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o-mini"

def load_prompt(name: str) -> str:
    path = os.path.join("prompts", f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ─── TOOL DEFINITIONS ────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_similar_cases",
            "description": "Pobiera z bazy zweryfikowane przypadki podobnych sylwetek. Używaj gdy potrzebujesz porównać analizę z wcześniejszymi zatwierdzonymi przez stylistkę.",
            "parameters": {
                "type": "object",
                "properties": {
                    "body_type": {
                        "type": "string",
                        "description": "Typ sylwetki: A (trójkąt), H (prostokąt), X (klepsydra), V (odwrócony trójkąt), O (owal)",
                        "enum": ["A", "H", "X", "V", "O"]
                    },
                    "style_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista tagów stylistycznych"
                    }
                },
                "required": ["body_type"]
            }
        }
    }
]

def handle_tool_call(tool_name: str, tool_args: dict) -> str:
    if tool_name == "get_similar_cases":
        cases = get_similar_cases(
            body_type=tool_args.get("body_type"),
            style_tags=tool_args.get("style_tags", [])
        )
        return json.dumps(cases, ensure_ascii=False)
    return json.dumps({"error": "nieznane narzędzie"})

# ─── ANALIZA SYLWETKI ─────────────────────────

def analyze_sylwetka(photo_url: str, ankieta: dict) -> dict:
    prompt_template = load_prompt("analiza_sylwetki")
    prompt = prompt_template.replace("{ankieta}", json.dumps(ankieta, ensure_ascii=False, indent=2))

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": photo_url,
                        "detail": "low"
                    }
                }
            ]
        }
    ]

    # Pierwsza próba — z tool calling (model może sięgnąć do bazy RAG)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=400,
        temperature=0.3
    )

    msg = response.choices[0].message

    # Obsługa tool callingu
    if msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            result = handle_tool_call(
                tool_call.function.name,
                json.loads(tool_call.function.arguments)
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # Drugi call z wynikami narzędzi
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1500,
            temperature=0.3
        )
        msg = response.choices[0].message

    raw = msg.content.strip()

    # Czyszczenie na wypadek gdyby model dodał markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "error": "Nie udało się sparsować odpowiedzi AI",
            "raw": raw
        }

# ─── SZYBKA ODPOWIEDŹ TEKSTOWA ───────────────

def quick_text(system_prompt: str, user_message: str, max_tokens: int = 800) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=max_tokens,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()
