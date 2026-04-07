import asyncio
import edge_tts

async def dump_events():
    text = "Hola, probando eventos de Edge."
    voice = "es-MX-DaliaNeural"
    communicate = edge_tts.Communicate(text, voice)
    
    print(f"Buscando eventos en {voice}...")
    async for chunk in communicate.stream():
        if chunk["type"] != "audio":
            print(f"EVENTO NO-AUDIO: {chunk}")
        else:
            print(f"Audio chunk recebido: {len(chunk['data'])} bytes")

if __name__ == "__main__":
    asyncio.run(dump_events())
