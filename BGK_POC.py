import streamlit as st
import requests
import json

st.title("🤖 watsonx.ai")

API_KEY = "Twój_api_key"
DEPLOYMENT_URL = "Twój_URL"

# --- Pobranie tokenu IAM ---
def get_token(api_key: str) -> str:
    url = "https://iam.cloud.ibm.com/identity/token"
    resp = requests.post(url, data={"apikey": api_key, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"})
    return resp.json()["access_token"]

# --- Funkcja do zapisywania konwersacji ---
def save_conversation(user_msg: str, assistant_msg: str, filename: str = "Ścieżka_do_pliku.txt"): #Tu wstaw ścieżkę do pliku
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"User: {user_msg}\n")
        f.write(f"watsonx.ai: {assistant_msg}\n")
        f.write("-" * 40 + "\n")

if "mltoken" not in st.session_state:
    st.session_state["mltoken"] = get_token(API_KEY)

# --- Sesja rozmowy ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Jesteś pomocnym asystentem AI od IBM. Udzielasz wyczerpujących odpowiedzi na zadane pytanie bazując na swojej bazie wiedzy. Jeśli nie znasz odpowiedzi po prostu odpowiedz: Nie wiem. Odpowiadaj tylko w języku polskim."}
    ]

# --- Wyświetl poprzednie wiadomości ---
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Obsługa inputu użytkownika ---
if prompt := st.chat_input("Zadaj mi pytanie :)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Wysyłanie zapytania do Watsonx ---
    headers = {"Authorization": "Bearer " + st.session_state["mltoken"]}
    payload = {"messages": st.session_state.messages}

    collected_text = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        with requests.post(DEPLOYMENT_URL, headers=headers, json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        try:
                            data = json.loads(decoded[len("data: "):])
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    collected_text += delta["content"]
                                    placeholder.markdown(collected_text)
                        except:
                            pass
    st.session_state.messages.append({"role": "assistant", "content": collected_text})

    # --- Zapisz konwersację do pliku ---
    save_conversation(prompt, collected_text)