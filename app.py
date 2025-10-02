import streamlit as st
import json
import os
import pandas as pd
import numpy as np
import pydeck as pdk
from openai import OpenAI # type: ignore
import faiss # type: ignore
import fitz  # type: ignore # PyMuPDF for PDFs

# ---------- Init OpenAI ----------
client = OpenAI(api_key="YOUR_OPENAI_API_KEY") 

# ---------- File to store users ----------
USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f)

# ---------- Signup ----------
def signup():
    st.subheader("Create a New Account ✨")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        users = load_users()
        if username in users:
            st.error("⚠ Username already exists. Try another.")
        elif password != confirm_password:
            st.error("⚠ Passwords do not match.")
        elif len(username.strip()) == 0 or len(password.strip()) == 0:
            st.error("⚠ Username and password cannot be empty.")
        else:
            users[username] = password
            save_users(users)
            st.success("✅ Account created successfully! Please login now.")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.rerun()

# ---------- Login ----------
def login():
    st.subheader("Login to Your Account 🔑")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"✅ Welcome back, {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

# ---------- Custom Styles ----------
def apply_custom_styles(theme="light"):
    if theme == "light":
        main_bg = "linear-gradient(-45deg, #f3e6ff, #e6f0ff, #f9e6ff, #e6f9ff)"
        sidebar_bg = main_bg
        text_color = "#2b2b2b"
        card_bg = "rgba(230, 230, 250, 0.9)"
        button_bg = "#D8BFD8"          # Soft pastel purple
        button_hover_bg = "#CBA0DC"    # Darker pastel for hover
        input_bg = "#ffffff"
        input_text = "#2b2b2b"
        placeholder_color = "#777777"
        tab_bg = "#D8BFD8"
        tab_text = "#2b2b2b"

    else:  # dark theme
        main_bg = "linear-gradient(-45deg, #2c3e50, #1a252f, #2c3e50, #141e30)"
        sidebar_bg = "linear-gradient(180deg, #141e30, #243b55)"
        text_color = "#f5f5f5"
        card_bg = "rgba(255, 255, 255, 0.08)"
        button_bg = "#3a506b"
        button_hover_bg = "#5a6f8c"
        input_bg = "#1e2a38"          # input box background
        input_text = "#f5f5f5"        # input text color
        placeholder_color = "#cccccc" # placeholder text
        tab_bg = "#3a506b"            # tab background
        tab_text = "#f5f5f5"          # tab text color

    st.markdown(f"""
    <style>
    /* Main container */
    [data-testid="stAppViewContainer"] {{
        background: {main_bg};
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: {text_color};
        font-family: 'Segoe UI', sans-serif;
    }}
    @keyframes gradientBG {{
        0% {{ background-position:0% 50%; }}
        50% {{ background-position:100% 50%; }}
        100% {{ background-position:0% 50%; }}
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        color: {text_color} !important;
        padding: 20px;
        border-right: 2px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease-in-out;
    }}
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    [data-testid="stSidebar"] button {{
        background-color: {button_bg} !important;
        color: {text_color} !important;
        border-radius: 12px;
        padding: 10px 20px;
        margin: 5px 0;
        border: none;
        width: 100%;
        transition: all 0.3s ease-in-out;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: {button_hover_bg} !important;
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 20px rgba(255,255,255,0.25);
    }}

    /* Metric cards */
    .metric-card {{
        background: {card_bg};
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0px 8px 25px rgba(0,0,0,0.2);
    }}

    /* Inputs, textareas, selects */
    input, textarea, select {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid {'#ccc' if theme=='light' else '#3a506b'} !important;
        border-radius: 6px !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {placeholder_color} !important;
        opacity: 1;
    }}

    /* Streamlit buttons */
    button[data-baseweb] {{
        background-color: {button_bg} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }}
    button[data-baseweb]:hover {{
        background-color: {button_hover_bg} !important;
        transform: scale(1.05);
        box-shadow: 0px 4px 15px rgba(138,43,226,0.4);
    }}

    /* Tabs for login/signup */
    [role="tab"] {{
        background-color: {tab_bg} !important;
        color: {tab_text} !important;
        border-radius: 8px !important;
        padding: 8px 20px;
        margin-right: 5px;
    }}
    [role="tab"][aria-selected="true"] {{
        background-color: {button_hover_bg} !important;
        color: {text_color} !important;
    }}

    /* Chat input box */
    [data-testid="stChatInputTextArea"] textarea {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
    }}
    [data-testid="stChatInputTextArea"] textarea::placeholder {{
        color: {placeholder_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ---------- Theme Toggle ----------
def theme_toggle():
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"
    col1, col2 = st.columns([8,1])
    with col2:
        if st.button("🌙" if st.session_state["theme"]=="light" else "☀️"):
            st.session_state["theme"] = "dark" if st.session_state["theme"]=="light" else "light"
            st.rerun()
    apply_custom_styles(st.session_state["theme"])

# ---------- FAISS Helpers ----------
def embed_texts(texts):
    embeddings = []
    for t in texts:
        emb = client.embeddings.create(input=t, model="text-embedding-3-small").data[0].embedding
        embeddings.append(emb)
    return np.array(embeddings).astype("float32")

def build_faiss_index(texts):
    embeddings = embed_texts(texts)
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

# ---------- Chatbot ----------
def chatbot_ui():
    st.title("🤖 Travel Assistant Chatbot")
    st.write("Upload documents and ask questions with context!")

    if "docs_texts" not in st.session_state:
        st.session_state.docs_texts = []
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    uploaded_file = st.file_uploader("Upload a document", type=["txt","csv","pdf"])
    if uploaded_file:
        if uploaded_file.type=="text/plain":
            text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type=="text/csv":
            df = pd.read_csv(uploaded_file)
            text = df.to_string()
        elif uploaded_file.type=="application/pdf":
            pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = " ".join([page.get_text() for page in pdf])
        else: text=""
        if text:
            st.session_state.docs_texts.append(text)
            st.session_state.vector_store = build_faiss_index(st.session_state.docs_texts)
            st.success("✅ Document added to knowledge base!")

    user_input = st.chat_input("Ask a question...")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        context=""
        if st.session_state.vector_store is not None:
            query_emb = embed_texts([user_input])
            D,I = st.session_state.vector_store.search(query_emb, k=2)
            retrieved = [st.session_state.docs_texts[i] for i in I[0] if i<len(st.session_state.docs_texts)]
            context="\n".join(retrieved)

        messages=[{"role":"system","content":"You are a travel assistant chatbot. Use context if provided."},
                  {"role":"system","content":f"Context: {context}"}]+[{"role":r,"content":m} for r,m in st.session_state.chat_history]

        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = response.choices[0].message["content"]
        st.session_state.chat_history.append(("assistant", reply))

    for role,msg in st.session_state.chat_history:
        if role=="user":
            st.chat_message("user").markdown(msg)
        else:
            st.chat_message("assistant").markdown(msg)

# ---------- Main ----------
def main():
    st.set_page_config(page_title="Tourism Analytics", layout="wide")
    theme_toggle()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"]=False

    if not st.session_state["logged_in"]:
        st.title("Welcome To Data Visualization of Global Travel and Holidays Website")
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Signup"])
        with tab1: login()
        with tab2: signup()
    else:
        menu = {
            "Home":"🏠","Dashboard":"📊","Trends & Forecasts":"📈","Interactive Map":"🗺",
            "Chatbot":"🤖","Feedback":"💬","Docs":"📄","Logout":"🚪"
        }
        st.sidebar.markdown("<div class='sidebar-title'></div>", unsafe_allow_html=True)
        for page, icon in menu.items():
            if st.sidebar.button(f"{icon} {page}"):
                if page=="Logout":
                    st.session_state["logged_in"]=False
                    st.session_state.pop("username", None)
                    st.rerun()
                else:
                    st.session_state["page"]=page
                    st.rerun()

        page = st.session_state.get("page","Home")

        # ----- Pages -----
        if page=="Home":
            st.title("🌍 Global Tourism & Revenue Insights Dashboard")
            st.markdown("Welcome to the *Global Tourism & Revenue Insights Dashboard* — your one-stop view for analyzing international tourism trends, financial flows, and holiday patterns.")
            st.subheader("Dashboard Sections")
            col1,col2,col3 = st.columns(3, gap="medium")
            col1.markdown('<div class="metric-card">💰<h3>Inbound & Outbound Revenue</h3><p>Track how countries generate and spend tourism revenue effectively.</p></div>', unsafe_allow_html=True)
            col2.markdown('<div class="metric-card">✈<h3>Arrivals & Departures</h3><p>Understand international visitor dynamics and seasonal trends.</p></div>', unsafe_allow_html=True)
            col3.markdown('<div class="metric-card">🎉<h3>Global Holiday Tourism</h3><p>Explore the impact of global holidays on tourism flows and popular destinations.</p></div>', unsafe_allow_html=True)
            st.success("✨ Use the sidebar to navigate through sections and explore insights interactively!")
        
        elif page=="Dashboard":
            st.title("📊 Dashboard")
            col1,col2,col3 = st.columns(3)
            col1.markdown('<div class="metric-card">💰<br>1.2 Trillion<br>Global Tourism Revenue</div>', unsafe_allow_html=True)
            col2.markdown('<div class="metric-card">✈<br>900M+<br>International Arrivals</div>', unsafe_allow_html=True)
            col3.markdown('<div class="metric-card">🎉<br>150+<br>Global Festivals Tracked</div>', unsafe_allow_html=True)
            dashboard_url = "https://app.powerbi.com/view?r=eyJrIjoiNWZhNzI2MDctM2M1YS00NWM3LThiYzEtNzYwMzk0ZWY2YjIyIiwidCI6ImUzYzVlN2ZkLWJhMDktNDJjNC05YjczLTllNTBjODBlZjE1YiJ9"
            st.components.v1.iframe(dashboard_url, height=650, scrolling=True)
        
        elif page=="Trends & Forecasts":
            st.title("📈 Tourism Trends & Forecasts")
            years=np.arange(2010,2031)
            revenue=np.linspace(500,1200,len(years))+np.random.randint(-50,50,len(years))
            st.line_chart(pd.DataFrame({"Year":years,"Revenue (Billion $)":revenue}).set_index("Year"))
        
        elif page=="Interactive Map":
            st.title("🗺 Interactive Tourism Hotspots Map")
            df=pd.DataFrame({"lat":[48.8566,40.7128,35.6895,-33.8688],"lon":[2.3522,-74.0060,139.6917,151.2093],"city":["Paris","New York","Tokyo","Sydney"],"tourists_million":[19.1,13.6,15.2,10.5]})
            st.pydeck_chart(pdk.Deck(
                initial_view_state=pdk.ViewState(latitude=20,longitude=0,zoom=1),
                layers=[pdk.Layer("ScatterplotLayer",data=df,get_position='[lon, lat]',get_radius="tourists_million*50000",get_color="[200,30,0,160]",pickable=True)],
                tooltip={"text":"{city}: {tourists_million}M visitors"}))
        
        elif page=="Chatbot": chatbot_ui()
        
        elif page=="Feedback":
            st.title("💬 Feedback")
            feedback=st.text_area("Your feedback")
            if st.button("Submit Feedback"): st.success("✅ Thank you for your feedback!")
        
        elif page=="Docs":
            st.title("📄 Documentation")
            theme=st.session_state.get("theme","light")
            docs_bg="rgba(50,50,60,0.8)" if theme=="dark" else "rgba(230,230,250,0.9)"
            docs_color="#f5f5f5" if theme=="dark" else "#000000"
            st.markdown(f"""
            <div style='background:{docs_bg}; color:{docs_color}; padding:20px; border-radius:15px;'>
            <h3>🔍 About this Project</h3>
            <p>The <b>Tourism Analytics Dashboard</b> is a comprehensive web application built using <b>Streamlit</b>,
            integrating <b>Power BI visualizations</b>, interactive maps, and AI-driven insights to analyze 
            global tourism trends, revenue, and visitor patterns.</p>
            <h3>⚙ How it Works</h3>
            <ul>
                <li><b>User Signup/Login</b> – Secure user authentication.</li>
                <li><b>Interactive Dashboard</b> – Key tourism metrics & global festivals.</li>
                <li><b>Trends & Forecasts</b> – Historical & projected revenue trends.</li>
                <li><b>Interactive Map</b> – Visualizes tourism hotspots worldwide.</li>
                <li><b>Chatbot</b> – AI assistant using FAISS for context-aware responses.</li>
                <li><b>Feedback Collection</b> – Submit feedback for improvements.</li>
            </ul>
            <h3>🚀 Future Enhancements</h3>
            <ul>
                <li>AI-driven analytics & predictive models.</li>
                <li>Live data integration for real-time updates.</li>
                <li>Customizable themes (light/dark toggle).</li>
                <li>Multilingual support for RAG chatbot.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

if __name__=="__main__":
    main()
