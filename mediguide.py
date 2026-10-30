from __future__ import annotations
import os
import json
import streamlit as st
import pandas as pd
from openai import OpenAI
from fpdf import FPDF
from audio_recorder_streamlit import audio_recorder

st.set_page_config(
    page_title="MediGuide AI - Medical Assistant",
    page_icon="🩺",
    layout="wide"
)

# --- THEME CONFIGURATION & CUSTOM CSS ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light (Green & Pink)"

def apply_theme():
    if st.session_state.theme_mode == "Light (Green & Pink)":
        return """
            <style>
            .stApp { background-color: #f4fbf7; color: #1b5e20; }
            h1, h2, h3 { color: #1b5e20 !important; }
            .stButton>button {
                background-color: #2e7d32; color: white; border-radius: 8px; font-weight: 600; border: none; transition: 0.3s ease;
            }
            .stButton>button:hover { background-color: #d81b60; color: white; }
            [data-testid="stSidebar"] { background-color: #e8f5e9; border-right: 2px solid #f8bbd0; }
            </style>
        """
    else:
        return """
            <style>
            .stApp { background-color: #121212; color: #e0e0e0; }
            h1, h2, h3 { color: #81c784 !important; }
            .stButton>button {
                background-color: #388e3c; color: white; border-radius: 8px; font-weight: 600; border: none;
            }
            .stButton>button:hover { background-color: #c2185b; color: white; }
            [data-testid="stSidebar"] { background-color: #1e1e1e; border-right: 2px solid #c2185b; }
            </style>
        """

st.markdown(apply_theme(), unsafe_allow_html=True)

# Session State initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = []
if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""

def generate_pdf_report(data_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="MediGuide AI - Patient Assessment Report", ln=True, align="center")
    pdf.ln(10)
    
    for key, value in data_dict.items():
        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(200, 8, txt=f"{key.upper()}:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, txt=str(value))
        pdf.ln(4)
        
    return pdf.output(dest='S').encode('latin1')

def main():
    # --- STEP 1: API Key Entry Screen ---
    col_img1, col_title, col_img2 = st.columns([1, 3, 1])
    with col_img1:
        st.image("https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    with col_title:
        st.title("🩺 MediGuide AI - Authentication")
        st.markdown("<p style='color: #d81b60; font-weight: 600;'>Your intelligent medical assistant partner with voice input & advanced features.</p>", unsafe_allow_html=True)
    with col_img2:
        st.image("https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    entered_key = st.text_input("Enter your OpenAI API Key to proceed:", type="password", value=st.session_state.api_key)
    
    if st.button("Login / Start App"):
        if entered_key.strip():
            st.session_state.api_key = entered_key.strip()
            st.rerun()
        else:
            st.error("⚠️ Please enter a valid OpenAI API key first!")
            
    if not st.session_state.api_key:
        st.info("💡 To begin the application workflow, please enter your OpenAI API key above and click the button.")
        return

    # --- STEP 2: Main Project Dashboard ---
    client = OpenAI(api_key=st.session_state.api_key)

    # Sidebar - Disclaimers & Bonus Controls (Theme Toggle & Language)
    with st.sidebar:
        st.image("https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=400&q=80", use_container_width=True)
        st.title("🩺 MediGuide AI")
        st.markdown("---")
        st.error("⚠️ **MEDICAL DISCLAIMER:**\n\nThis application is an educational prototype only[cite: 1]. It is NOT a replacement for a licensed doctor or emergency service[cite: 1].")
        st.markdown("---")
        st.subheader("⚙️ Settings & Bonus Controls")
        
        selected_theme = st.selectbox("Theme Mode", ["Light (Green & Pink)", "Dark Mode"], index=0 if st.session_state.theme_mode == "Light (Green & Pink)" else 1)
        if selected_theme != st.session_state.theme_mode:
            st.session_state.theme_mode = selected_theme
            st.rerun()
            
        selected_model = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-4o"])
        language = st.selectbox("Answer Language", ["English", "Urdu", "Spanish", "French"])
        
        if st.button("Logout / Change API Key"):
            st.session_state.api_key = ""
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 📊 Analytics Overview")
        if st.session_state.analytics_data:
            df_analytics = pd.DataFrame(st.session_state.analytics_data)
            st.metric("Total Assessments", len(df_analytics))
        else:
            st.info("No assessments recorded yet.")

    # Main Header with Banner Image
    st.image("https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    st.title("AI-Powered Medical Symptom Assessment & Guidance Assistant")
    st.write("Enter your symptoms and details below or use **Voice Input** to receive structured preliminary guidance.")

    # Tabs for Main App and Bonus Features
    tab_form, tab_history, tab_analytics = st.tabs(["📝 Symptom Assessment", "📜 Patient History (Bonus)", "📊 Analytics Dashboard (Bonus)"])

    with tab_form:
        # --- Voice Input Feature Widget ---
        st.markdown("### 🎙️ Voice Symptom Recorder (Bonus Feature)")
        st.write("Record your symptoms verbally using your microphone:")
        
        audio_bytes = audio_recorder(text="Click to record voice symptoms", icon_size="2x", icon_name="microphone")
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            with st.spinner("Transcribing audio via OpenAI Whisper..."):
                try:
                    # Save temporary audio file for Whisper API transcription
                    temp_audio_path = "temp_voice_note.wav"
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    with open(temp_audio_path, "rb") as audio_file:
                        transcript_res = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                        st.session_state.voice_transcript = transcript_res.text
                    
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                        
                    st.success(f"🗣️ Transcription successful: \"{st.session_state.voice_transcript}\"")
                except Exception as e:
                    st.warning(f"Voice transcription note: {e}. (Make sure a valid OpenAI API key with audio permissions is provided).")

        st.markdown("---")
        
        with st.form("medical_form"):
            col1, col2 = st.columns(2)
            with col1:
                age = st.text_input("Patient Age", "25")
                gender = st.selectbox("Gender", ["Female", "Male", "Other"])
                symptoms = st.multiselect("Select Symptoms", ["Runny Nose", "Sore Throat", "Fever", "Cough", "Severe Chest Pain", "Shortness of Breath", "Headache"])
                duration = st.selectbox("Duration of Symptoms", ["1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks"])
            with col2:
                severity = st.slider("Severity Level (1-10)", 1, 10, 3)
                existing_conditions = st.text_area("Existing Medical Conditions", "None")
                current_medications = st.text_area("Current Medications", "None")
                
                # Combine manual notes with any transcribed voice input
                default_notes = st.session_state.get("voice_transcript", "None")
                additional_notes = st.text_area("Additional Notes / Voice Transcript", value=default_notes)
            
            submitted = st.form_submit_button("Assess Symptoms")

        if submitted:
            if not symptoms and not st.session_state.get("voice_transcript"):
                st.warning("⚠️ Please select at least one symptom or record your voice symptoms before submitting.")
            else:
                with st.spinner("Analyzing symptoms securely..."):
                    prompt = f"""
                    You are MediGuide AI, an educational medical assistant prototype. Analyze the following patient data and return valid JSON with keys: 
                    'summary', 'possible_conditions' (list of dicts with 'name' and 'reason'), 'urgency_level' (LOW, MEDIUM, HIGH, EMERGENCY), 'recommended_next_steps', 'questions_for_doctor' (list), and 'warning_signs' (list).
                    
                    Language for response: {language}
                    Age: {age}
                    Gender: {gender}
                    Symptoms: {', '.join(symptoms)}
                    Duration: {duration}
                    Severity: {severity}/10
                    Existing Conditions: {existing_conditions}
                    Medications: {current_medications}
                    Notes & Voice Transcription: {additional_notes}
                    
                    Return ONLY raw JSON, no markdown code blocks if possible.
                    """
                    
                    try:
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=[
                                {"role": "system", "content": "You are a helpful medical assistant that outputs strictly in JSON format."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3
                        )
                        raw_text = response.choices[0].message.content.strip()
                        
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]
                            
                        parsed_data = json.loads(raw_text.strip())
                        
                        st.session_state.chat_history.append({"input": symptoms, "output": parsed_data})
                        st.session_state.analytics_data.append({"Urgency": parsed_data.get("urgency_level", "LOW")})

                        st.success("Assessment Complete!")
                        
                        st.subheader("📋 Results Dashboard")
                        urgency = parsed_data.get("urgency_level", "LOW").upper()
                        if urgency == "EMERGENCY" or urgency == "HIGH":
                            st.error(f"🚨 Urgency Level: {urgency} - Seek immediate medical help!")
                        elif urgency == "MEDIUM":
                            st.warning(f"⚠️ Urgency Level: {urgency} - Professional consultation advised.")
                        else:
                            st.success(f"🟢 Urgency Level: {urgency} - Monitor symptoms calmly.")
                            
                        st.info(f"**Summary:** {parsed_data.get('summary')}")
                        
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.markdown("### 🩺 Possible Conditions (Educational)")
                            for cond in parsed_data.get("possible_conditions", []):
                                st.write(f"- **{cond.get('name')}**: {cond.get('reason')}")
                                
                            st.markdown("### 🏃 Recommended Next Steps")
                            st.write(parsed_data.get("recommended_next_steps"))
                            
                        with col_res2:
                            st.markdown("### ❓ Questions for Doctor")
                            for q in parsed_data.get("questions_for_doctor", []):
                                st.write(f"- {q}")
                                
                            st.markdown("### ⚠️ Warning Signs")
                            for w in parsed_data.get("warning_signs", []):
                                st.write(f"- {w}")

                        # PDF Report Download
                        pdf_bytes = generate_pdf_report(parsed_data)
                        st.download_button(
                            label="📥 Download Guidance Report as PDF (Bonus Feature)",
                            data=pdf_bytes,
                            file_name="mediguide_report.pdf",
                            mime="application/pdf"
                        )

                    except Exception as e:
                        st.error(f"Error parsing response or connecting to OpenAI API: {e}")
                        st.write("Raw Output received:", raw_text if 'raw_text' in locals() else "No response")

    # Patient Session History Tab
    with tab_history:
        st.subheader("📜 Patient Session History (Bonus Feature)")
        if not st.session_state.chat_history:
            st.info("No past assessments recorded in this session yet.")
        else:
            for idx, item in enumerate(st.session_state.chat_history):
                with st.expander(f"Assessment #{idx+1} - Symptoms: {', '.join(item['input'])}"):
                    st.json(item['output'])

    # Analytics Dashboard Tab
    with tab_analytics:
        st.subheader("📊 Urgency Distribution Analytics (Bonus Feature)")
        if st.session_state.analytics_data:
            df_analytics = pd.DataFrame(st.session_state.analytics_data)
            urgency_counts = df_analytics['Urgency'].value_counts()
            st.bar_chart(urgency_counts)
        else:
            st.info("Perform an assessment to view analytics data.")

if __name__ == "__main__":
    main()