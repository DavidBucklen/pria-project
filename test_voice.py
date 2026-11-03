from voice import speak

print("Testing Kokoro voice system...\n")

speak(
    text="Hello. How are you today?",
    voice="af_heart",
    speed=1.0,
    emotion="affection"
)

input("\nPress Enter to exit...")