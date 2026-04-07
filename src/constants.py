EVERGREEN_TOPICS = [
    "Psicología Humana",
    "Comportamiento Social",
    "Misterios del Universo",
    "Hábitos Exitosos",
    "Paradojas Temporales",
    "Biología Marina Extraña",
    "Historia Oculta",
    "Filosofía Estoica",
    "Efecto Placebo",
    "Lenguaje Corporal"
]

WHAT_IF_TOPICS = [
    "Si todos fuéramos millonarios",
    "Si los humanos pudieran volar",
    "Si el internet dejara de existir",
    "Si viviéramos bajo el agua",
    "Si nunca tuviéramos sueño",
    "Si los dinosaurios siguieran vivos",
    "Si pudiéramos leer mentes",
    "Si el sol se apagara por 1 hora",
    "Si la gravedad desapareciera por 5 segundos",
    "Si todos los insectos del mundo atacaran a la vez",
    "Si la Tierra fuera del tamaño de Júpiter",
    "Si pudiéramos teletransportarnos",
    "Si dejara de llover para siempre",
    "Si la Luna desapareciera de repente",
    "Si los animales pudieran hablar",
    "Si tuviéramos visión de rayos X",
    "Si el oxígeno se duplicara en la atmósfera",
    "Si todos fuéramos inmortales",
    "Si los robots tomaran el control",
    "Si pudiéramos viajar en el tiempo",
    "Si solo comiéramos una vez al año",
    "Si los humanos tuvieran clorofila",
    "Si el hielo de los polos se derritiera hoy",
    "Si pudiéramos descargar conocimientos al cerebro",
    "Si viviéramos en Marte",
    "Si el dinero dejara de tener valor",
    "Si pudiéramos ver el futuro",
    "Si la Tierra dejara de girar",
    "Si fuéramos la única especie en la Tierra",
    "Si pudiéramos respirar en el espacio"
]

TOP_3_TOPICS = [
    "Top 3 Lugares más extraños de la Tierra",
    "Top 3 Animales que parecen alienígenas",
    "Top 3 Inventos futuristas que ya existen",
    "Top 3 Misterios del océano sin resolver",
    "Top 3 Ciudades perdidas en la historia",
    "Top 3 Fenómenos naturales inexplicables",
    "Top 3 coincidencias imposibles de creer",
    "Top 3 fobias más raras del mundo",
    "Top 3 tesoros que nunca fueron encontrados",
    "Top 3 lugares donde está prohibido entrar"
]

DARK_FACTS_TOPICS = [
    "El oscuro origen de los cuentos de hadas",
    "Experimentos médicos clasificados durante la Guerra Fría",
    "La verdadera historia detrás de Jack el Destripador",
    "El lado perturbador de la Revolución Industrial",
    "Pueblos fantasma y sus oscuras historias",
    "Tecnología antigua que no deberíamos haber olvidado",
    "Incidentes inexplicables en alta mar",
    "El sombrío trasfondo de canciones infantiles",
    "Desapariciones históricas sin resolver",
    "Sociedades secretas que cambiaron el mundo"
]

HISTORY_TOPICS = [
    "El misterio sin resolver de la Colonia Roanoke",
    "La oscura verdad detrás del hundimiento del Titanic",
    "Los aterradores secretos de Prípiat y Chernóbil",
    "La conspiración detrás de la Mona Lisa",
    "El increíble y único escape real de Alcatraz",
    "La verdad oculta sobre la vida de Cleopatra",
    "El vuelo 19 y los secretos del Triángulo de las Bermudas",
    "El extraño caso del Paso Diátlov",
    "Los aterradores secretos de la Inquisición",
    "La verdad histórica del Rey Arturo y Excalibur"
]

CUSTOM_TOPICS = [
    "Tema sugerido por la IA",
    "Curiosidades aleatorias",
    "Datos poco conocidos del siglo XXI"
]

# Smart Music Mapping
# Determine emotion -> Select file
MUSIC_MOODS = {
    "mystery": ["the_mystery.mp3", "science_fiction.mp3", "deep_mystery.wav", "dark_tension.wav"],
    "happy": ["happy_life.mp3", "upbeat_energy.wav"],
    "epic": ["cinemato.mp3", "epic_battle.wav"],
    "curiosity": ["planning.mp3", "science_fiction.mp3", "deep_mystery.wav"],
    "sad": ["planning.mp3", "emotional_piano.wav"],
    "dark": ["the_mystery.mp3", "science_fiction.mp3", "dark_tension.wav"]
}

# Branding
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Montserrat-ExtraBold.ttf")
