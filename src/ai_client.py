import os
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv

load_dotenv()

def generate_script(topic=None, specific_hook=None, style="curiosity", is_test=False, lang="en"):
    """

    Generates a 3-sentence script for a YouTube Short using Google Gemini (New SDK).
    Returns a dictionary with 'hook', 'body', 'climax', 'title', 'hashtags'.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    if style == "what_if":
        if topic:
             topic_instruction = f"TOPIC: 'What would happen if {topic}?'. Generate a speculative scientific/social scenario."
        else:
             topic_instruction = "TOPIC: Choose a RANDOM 'What If' scenario (e.g. What if the moon disappeared? What if we never slept?)."
             
        system_instruction = """
        STYLE: "WHAT IF" SCENARIO.
        - Hook: MUST start with "¿Qué pasaría si..." or "Imagina si...".
        - Body: logical but dramatic consequences based on REAL physics, REAL science, or REAL historical data. Do NOT invent fictional characters.
        - Climax: existential or mind-blowing conclusion.
        """
    elif style == "top_3":
         if topic:
             topic_instruction = f"TOPIC: '{topic}'."
         else:
             topic_instruction = "TOPIC: Choose a RANDOM 'Top 3' list (e.g. Top 3 Most Dangerous Roads)."
         
         system_instruction = """
         STYLE: "TOP 3 RANKING" (Viral Countdown).
         STRUCTURE (MANDATORY):
         - HOOK (2-3 scenes): Start with the BIGGEST mystery or the most shocking fact about the #1 spot without revealing what it is. Generate an immediate need to know.
         - POSITION 3 (3-4 scenes): Introduce it naturally. Example: 'Empezamos con algo que desafía la física...', 'En el lugar 3 tenemos...'.
             * The narration must focus on the SHOCK VALUE. 
             * Give: Year/Name, a concrete achievement, and ONE bizarre detail.
         - POSITION 2 (3-4 scenes): Use a transition that builds tension. 'Pero si creías que eso era raro, mira esto...'.
         - POSITION 1 (3-4 scenes): The climax. 'Finalmente, el puesto que todos esperaban...'. Explain WHY it's the undisputed winner.
         - CONCLUSION (1 scene): A final thought that connects all three or poses a question to the viewer.
         TONE: Enthusiastic, fast-paced, like a high-end documentary.
         CRITICAL: Every scene MUST have a specific name or number. ZERO filler sentences.
         """
    elif style == "dark_facts":
         if topic:
             topic_instruction = f"TOPIC: '{topic}'. Focus on the most unsettling, mysterious, or mind-blowing psychological/historical facts."
         else:
             topic_instruction = "TOPIC: Choose a RANDOM 'Dark Fact' or disturbing truth that is SHOCKING and forces the viewer to think 'how is this possible?'."
         
         system_instruction = """
         STYLE: "VIRAL MYSTERY" / PSYCHOLOGICAL DARKNESS.
         - Hook: NEVER start with 'Sabías que'. START with a shocking statement or a terrifying question.
         - Examples: 'Tu cerebro te está mintiendo ahora mismo...', 'El gobierno ocultó esto por 50 años...', 'Lo que ocurre en este lugar desafía la lógica...'.
         - Tone: Suspenseful, whisper-like intensity, cinematic.
         - CRITICAL: Use REAL cases but emphasize the 'horror' or 'unexplained' aspect.
         - Climax: A final revelation that makes the viewer feel uncomfortable or amazed.
         """
    elif style == "history":
         if topic:
             topic_instruction = f"TOPIC: '{topic}'. Focus on the most mind-blowing, cinematic, and VIRAL angles of this historical event."
         else:
             topic_instruction = "TOPIC: Choose a RANDOM epic historical event or figure. CRITICAL: It MUST be a widely recognized topic with a mind-blowing twist. STRICTLY AVOID obscure, boring wars or irrelevant academic figures that nobody cares about."
         
         system_instruction = """
         STYLE: "VIRAL HISTORY" / MODERN DOCUMENTARY.
         - Hook: MUST start with "La historia no contada de..." or "Así fue como...".
         - Tone: Epic, dramatic, fast-paced, but explain it simply and with a touch of wit. No boring textbook definitions.
         - CRITICAL: STRICTLY Factual. Use REAL historical names, REAL verified locations, and REAL verified dates. No fictional dramatizations.
         - Climax: Emphasize a shocking twist or massive historical impact.
         """
    elif style == "custom":
         if topic:
             topic_instruction = f"TOPIC: '{topic}'. Create a highly engaging script EXACTLY about this specific request."
         else:
             topic_instruction = "TOPIC: Choose a RANDOM highly engaging topic since no custom prompt was provided."
         
         system_instruction = """
         STYLE: "CUSTOM REQUEST".
         - Hook: Directly address the core of the requested topic immediately.
         - Tone: Highly engaging, dynamic, simple to understand, and with a touch of wit/humor. No boring textbook definitions.
         - Structure: Hook -> Fascinating & Witty Body -> Strong Conclusion.
         - CRITICAL: If the prompt implies real-world topics (like sports, history, science), you MUST use 100% REAL facts, REAL names, and REAL verified information. NEVER hallucinate fictional generic examples.
         """
    else:
        # Default Curiosity / Storytelling
        if topic and not specific_hook:
            topic_instruction = f"TOPIC: '{topic}'. Create a script that reveals a SHOCKING SECRET or a COUNTER-INTUITIVE truth about this."
        elif specific_hook:
            topic_instruction = f"START EXACTLY WITH THIS HOOK: '{specific_hook}'. Then build a story around it."
        else:
            topic_instruction = "TOPIC: Choose a RANDOM topic that sounds like a 'Hidden Truth' or a 'Bizarre Reality' (e.g., hidden rooms in famous places, weird laws, animal superpowers)."
        
        system_instruction = """
        STYLE: VIRAL STORYTELLER / HIGH RETENTION.
        - The Goal: Make the user forget they are watching a video and get lost in the story.
        - Narrative Arc: Start with a mystery, build tension with 3 shocking details, and end with a 'mind-blown' realization.
        - NO 'AI language': Avoid words like 'fascinante', 'increíble', 'asombroso'. Use everyday but impactful words.
        - Pacing: Fast, punchy, no redundant words.
        """

    test_instruction = ""
    if is_test:
        test_instruction = """
        *** CRITICAL: THIS IS A SHORT DEMO TEST. ***
        THE SCRIPT MUST BE EXTREMELY SHORT (MAXIMUM 10 SECONDS OF SPEECH).
        ONLY GENERATE EXACTLY 2 SCENES: 1 VERY SHORT HOOK AND 1 IMMEDIATE OUTRO.
        """
        
    lang_name = "SPANISH (ESPAÑOL)" if lang == "es" else "ENGLISH"
    # Determine if this style uses perfect loop
    uses_perfect_loop = style in ("curiosity", "what_if")
    loop_rule = """
    4. **PERFECT LOOP (CRITICAL RULE)**: 
       - The FINAL sentence of the script MUST connect grammatically and logically back to the hook (the FIRST sentence).
       - EXAMPLE: If Hook is "This goal changed football forever...", the Climax (End) MUST be "...and that is why this goal changed football forever."
       - This creates a seamless infinite playback loop for YouTube Shorts. Do this for EVERY script.
    """ if uses_perfect_loop else """
    4. **ENDING RULE**: The final scene must be a strong, satisfying close — a memorable fact, a provocative question, or a powerful statement. Do NOT loop back to the intro. This is a COMPLETE video, not a loop.
    """
    
    prompt = f"""
    You are not generating a background.
    You are generating a SHORT-FORM VIDEO PLAN where visuals must MATCH the narration moment by moment.
    
    {topic_instruction}
    {system_instruction}
    {test_instruction}
    
    TASK:
    1. Break script into **{"2 SHORT SCENES TOTAL" if is_test else "13 to 15 MICRO-SCENES MINIMUM"}**.
    2. Analyze the EMOTIONAL TONE (Mood) of the script.
    3. Generate VIRAL SEO METADATA (Title, Description, Tags).
    4. **TAGS OPTIMIZATION**:
       - Generate 15-20 high-traffic YouTube tags.
       - Mix broad keywords (e.g., "History", "Science") and specific long-tail keywords (e.g., "Hidden truths about Titanic").
       - **CRITICAL**: The `tags_string` field must be a SINGLE string of comma-separated tags.
       - **CRITICAL**: The total length of `tags_string` MUST BE under 500 characters.
    
    RULES:
    0. **STORYTELLING OVER FACTS (CRITICAL)**: While facts must be REAL, the way you tell them is what matters. Don't just list them. Connect them. Start with a "Curiosity Gap" (tell them what they DON'T know first). Never use intro phrases like 'En este video...', 'Hola a todos', or generic greetings. Jump STRAIGHT into the action.
    1. **Natural & Provocative Pacing**: Write like a human talking to a friend about something crazy they just found out. Use short, punchy sentences. Avoid being overly formal or "educational".
    2. **Viral Titles (SEO_TITLE)**: Generate titles that trigger FOMO (Fear Of Missing Out) or extreme curiosity. 
       - Bad: "3 Datos sobre Marte"
       - Good: "Lo que la NASA no te contó de Marte" o "Por esto nunca podremos vivir en Marte".
       - Use "The Reason Why", "The Secret of", "Nobody talks about this", "This is illegal in...".
    2. **Scenes Total**: {"ONLY 2 SCENES" if is_test else "13-15 Micro-Scenes Minimum. You MUST break down every single sentence into 2-3 visual beats. For TOP 3 style: each ranked item gets at least 3-4 scenes."}
    3. **Visual Variety**: Use different angles (close-up, wide, drone) for consecutive shots.
    {loop_rule}
    5. **Stock Footage Keywords (CRITICAL SURGICAL LITERALITY - IN ENGLISH)**:
       - `visual_search_term_en` MUST be a **CONCRETE, FILMABLE, REAL OBJECT** that a camera can physically record.
       - **CONTEXTUAL SPECIFICITY**: The visual MUST relate to the core topic. If the topic is football/soccer, use "soccer stadium", "soccer ball", "soccer player", NOT generic "man running".
       - **ABSOLUTE RULE**: It MUST be EXACTLY 1 to 3 words. No commas. No adjectives. No poetry.
       - **BAD (ABSTRACT/UNFINDABLE)**: "cosmic universe stars", "warped reality", "light speed effect", "mystery", "fear", "people", "particles", "abstract", "smoke effect", "light rays", "energy", "darkness".
       - **GOOD (REAL OBJECTS)**: "ancient temple", "skull", "laboratory", "sword", "human brain", "old book", "volcano", "medieval castle", "microscope", "skeleton", "prison cell", "hospital bed".
       - **RELEVANCE**: If the text talks about death, use "cemetery" or "skull" NOT "darkness". If the text talks about mystery, use "detective" or "magnifying glass" NOT "abstract lights".
       - Match the SUBJECT of what is being discussed. Think: "what would a filmmaker actually FILM for this scene?"
       - DO NOT hallucinate related concepts. IF you exceed 3 words, the system will CRASH.
       - NEVER use specific copyrighted names here (like "Harry Potter", "Ricardo Darin", "Star Wars"). Pexels doesn't have them. Use generic terms like "wizard", "man", "spaceship".
    6. **SPECIFIC ENTITIES — visual_overlay_term (MOST CRITICAL RULE OF ALL)**:
       - ASK YOURSELF for EVERY scene: "Does this scene mention a SPECIFIC named person, movie, TV show, city, building, brand, song, athlete, politician, or historical event?"
       - If YES → `visual_overlay_term` MUST be set. No exceptions.
       - If NO (the scene talks about a completely generic concept like 'time', 'nature', 'science', 'the universe') → `visual_overlay_term` = null.
       
       MANDATORY CASES — ALWAYS set `visual_overlay_term`:
       - Any ANIME, CARTOON, or VIDEO GAME by title or character → "Dragon Ball Z anime", "Goku escena", "Super Mario Bros", "Naruto Shippuden pelea"
       - Any MOVIE or TV SHOW by title → "El Clan pelicula", "Stranger Things serie", "The Dark Knight escena" (IMPORTANT: Prioritize the TITLE of the show, NOT the actors/directors, so we see the actual show!)
       - Any REAL PERSON (politician, athlete, musician, actor) → Append 'interview' or 'face' for best results: "Lionel Messi interview", "Albert Einstein face", "Freddie Mercury live", "Guillermo Francella cara"
       - Any COMPANY or BRAND → Append 'logo' or 'b-roll' for best results: "Netflix logo b-roll", "Disney company logo", "Apple iPhone b-roll", "Ferrari F40 driving"
       - Any SPECIFIC PLACE (famous building, city, landmark) → "Torre Eiffel", "Machu Picchu", "Buenos Aires drone"
       - Any HISTORICAL EVENT → "Segunda Guerra Mundial batalla", "Revolución Francesa pintura"
       
       FORBIDDEN (NEVER put these in visual_overlay_term, use null):
       - Generic adjectives: "genius", "funny", "dramatic", "epic battle"
       - Generic concepts: "cinema", "movies", "comedy", "acting", "drama", "anime", "fight"
       - Things that are already described generically in visual_search_term_en
       
       SEARCH QUALITY: Make the term EXACT and SEARCHABLE on YouTube/Google. Include the person's full name + the specific work if relevant.
       Example: NOT "El Clan" alone. YES: "Guillermo Francella El Clan pelicula".
    7. **LANGUAGE**: 
       - The `text` (script), `title`, and `hashtags` MUST be in **{lang_name}**.
       - `visual_search_term_en` MUST be in **ENGLISH**.
    8. **CRITICAL JSON FORMATTING**: 
       - NEVER use double quotes (") inside string values. If you need quotes, use single quotes (').
       - NEVER use line breaks inside string values.
       - The `visual_overlay_term` must be `null` (lowercase boolean, without quotes) if not used, NOT "Null" or the string "null".

    OUTPUT FORMAT (Pure JSON):
    {{
      "title": "Video Title ({lang_name})",
      "mood": "mystery" | "happy" | "epic" | "curiosity" | "sad",
      "seo_title": "CLICKBAIT Viral Title for YouTube Shorts ({lang_name})",
      "seo_description": "3-line SEO optimized description with keywords ({lang_name})",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
      "tags_string": "comma, separated, list, of, tags, under, 500, chars, for, youtube",
      "hashtags": ["#tag1", "#tag2"],
      "scenes": [
        {{
          "text": "Script text in {lang_name}...",
          "visual_search_term_en": "literal description of visual in English (NEVER use specific names/movies here)",
          "visual_overlay_term": "CRITICAL: Specific searchable exact name if talking about a film, actor, game, famous person, or brand (e.g. 'Ricardo Darin', 'Eiffel Tower', 'Breaking Bad'). null if the topic is fully generic.",
          "color_palette": "color1, color2",
          "subtitle_emphasis": ["emphasis word"]
        }},
        ...
      ]
    }}
    """

    import time
    
    max_retries = 3
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            
            text_response = response.text
            try:
                script_data = json.loads(text_response)
                return script_data
            except Exception as json_err:
                with open("bad_response.json", "w", encoding="utf-8") as f:
                    f.write(text_response)
                raise json_err
            
        except Exception as e:
            error_str = str(e)
            # Retry on rate limits OR network/dns errors
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "getaddrinfo failed" in error_str or "11001" in error_str:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (attempt + 1)
                    print(f"⚠️ Error transitorio ({e}). Reintentando en {wait_time}s... (Intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error: Fallaron los reintentos tras error: {e}")
                    return None
            else:
                print(f"Error generating script: {e}")
                return None

def generate_viral_hooks(base_topic, trending_list, lang="en"):
    """
    Generates 5 viral hook variations adapting a base topic with trending terms.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    lang_name = "SPANISH" if lang == "es" else "ENGLISH"
    prompt = f"""
    You are a hook adaptation engine for short-form viral videos.

    IMPORTANT:
    - ALL output must be in {lang_name}.
    - Do NOT generate full scripts.
    - Do NOT explain the topic.
    - Your ONLY task is to adapt HOOKS.

    INPUT YOU WILL RECEIVE:
    1) A BASE EVERGREEN TOPIC: "{base_topic}"
    2) A LIST OF CURRENT TRENDING TERMS: {trending_list}

    YOUR ROLE:
    - Use trending terms ONLY as contextual examples.
    - NEVER depend on the trend to explain the video.
    - The core meaning must stay evergreen.
    - Trends are optional flavor, not the core subject.

    RULES:
    - Do NOT mention news, dates, or events explicitly.
    - Do NOT explain the trend itself.
    - Do NOT sound like news content.
    - Hooks must sound natural, intriguing, and timeless.

    WHAT TO GENERATE:
    - Generate 5 SHORT HOOK VARIATIONS
    - Each hook must be 1 sentence
    - Max 12 words per hook
    - Use curiosity or contradiction
    - If no trend fits naturally, IGNORE it

    OUTPUT FORMAT (STRICT JSON):
    {{
      "hooks": [
        "texto",
        "texto",
        "texto",
        "texto",
        "texto"
      ]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text).get('hooks', [])
    except Exception as e:
        print(f"Error generating hooks: {e}")
        return []

def generate_creative_topic(style="what_if", lang="en"):
    """
    Asks the AI to invent a NEW, UNIQUE topic that is not in a standard list.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    lang_name = "SPANISH" if lang == "es" else "ENGLISH"
    
    if style == "what_if":
        prompt = f"""
        TASK: Invent a unique, mind-blowing 'What If' scenario for a YouTube Short.
        - Must be speculative, scientific, or philosophical.
        - profound or paradoxical.
        - EXAMPLES: "What if shadows were alive?", "What if silence killed you?", "What if dreams were shared reality?"
        - OUTPUT: Just the straight topic string in {lang_name}. No quotes.
        - DO NOT output generic ones like "zombies" or "aliens". Be creative.
        """
    elif style == "top_3":
        prompt = """
        TASK: Invent a unique "Top 3" list topic for a video.
        - Format: "Top 3 [Adjective] [Subject]"
        - Examples: "Top 3 lugares prohibidos", "Top 3 animales inmortales", "Top 3 sonidos más fuertes".
        - OUTPUT: Just the topic string in {lang_name}.
        """
    elif style == "dark_facts":
        prompt = """
        TASK: Invent a unique, disturbing or obscure 'Dark Fact' topic for a YouTube Short.
        - Must be a real but creepy historical event, psychological fact, or scientific reality.
        - Examples: "El experimento del sueño ruso", "La verdad sobre los cementerios victorianos".
        - OUTPUT: Just the topic string in {lang_name}.
        """
    elif style == "history":
        prompt = """
        TASK: Invent a unique, epic historical topic for a YouTube Short.
        - Focus on intense battles, lost empires, or misunderstood historical figures.
        - Examples: "El escuadrón perdido de Roma", "El arma secreta de Arquímedes".
        - OUTPUT: Just the topic string in {lang_name}.
        """
    elif style == "custom":
        prompt = """
        TASK: Invent a highly engaging, viral topic for a YouTube Short.
        - Combine pop culture, science, or mind-blowing concepts.
        - OUTPUT: Just the topic string in {lang_name}.
        """
    else:
        prompt = """
        TASK: Invent a specific, unique curiosity topic for a YouTube Short.
        - Must be obscure but fascinating.
        - OUTPUT: Just the topic string in {lang_name}.
        """
        
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"Error generating creative topic: {e}")
        return None

if __name__ == "__main__":
    # Test run
    print(generate_script())
 