import os
import threading
import streamlit as st
import telebot
from google import genai
from google.genai import types

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")

client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_PROMPT = (
    "Eres un asistente virtual inteligente, amable y conciso. "
    "Respondes dudas académicas, técnicas y generales de forma clara y estructurada."
)

def consultar_agente(mensaje_usuario: str) -> str:
    modelos = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
    ultimo_error = ""
    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=mensaje_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            ultimo_error = str(e)
            continue
    return f"Error al conectar con la IA: {ultimo_error}"

@st.cache_resource
def iniciar_bot_telegram():
    if not TG_TOKEN:
        return None
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=["start", "help"])
    def bienvenida(message):
        bot.reply_to(
            message,
            "¡Hola! Soy el agente desplegado. Escríbeme cualquier pregunta y te responderé al instante."
        )

    @bot.message_handler(func=lambda message: True)
    def responder_mensaje(message):
        bot.send_chat_action(message.chat.id, "typing")
        respuesta = consultar_agente(message.text)
        bot.reply_to(message, respuesta)

    hilo = threading.Thread(
        target=bot.infinity_polling,
        kwargs={"timeout": 20, "long_polling_timeout": 10},
        daemon=True
    )
    hilo.start()
    return bot

iniciar_bot_telegram()

st.set_page_config(page_title="Agente IA Web + Telegram", page_icon="🤖")
st.title("🤖 Agente Inteligente Desplegado")
st.caption("Conectado simultáneamente a esta interfaz web y a Telegram.")

if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"role": "assistant", "content": "¡Hola! Ya estoy activo en la web y en Telegram. ¿En qué te ayudo?"}
    ]

for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta = consultar_agente(prompt)
            st.markdown(respuesta)
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
