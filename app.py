import base64
import os
from analyser import pdf_to_jpg, process_image  # Import image processing functions
import streamlit as st
import pandas as pd
import plotly.graph_objects as go  

# Set page layout to "wide"
st.set_page_config(layout="wide")

# Page Navigation State
if "page" not in st.session_state:
    st.session_state.page = "main"

# Function to display project title
def show_project_title():
    st.markdown(
        """
        <h2 style="text-align: center; color: #4A90E2;">Resume Analysis</h2>
        """,
        unsafe_allow_html=True
    )

def show_loading_screen():
    """Displays a full-screen loading spinner while processing."""
    placeholder = st.empty()  # Create a placeholder for the spinner

    with placeholder.container():
        st.markdown(
            """
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.8); display: flex; justify-content: center;
                        align-items: center; color: white; font-size: 24px; font-weight: bold;">
                ⏳ Analyzing your resume... Please wait.
            </div>
            """,
            unsafe_allow_html=True
        )

    return placeholder  # Return the placeholder so it can be removed later

# Callback function to remove resume
def remove_resume():
    st.session_state.resume_uploaded = False
    st.session_state.uploaded_file = None
    st.rerun()

# Function to save uploaded file to root directory
def save_uploaded_file(uploaded_file):
    file_path = os.path.join(os.getcwd(), uploaded_file.name)  # Save in root directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path  # Return file path

# Function to display analytics page with extracted data
def show_analytics():
    show_project_title()  # Keep title on analytics page

    st.title("📊 Resume & Job Description Analytics")

    # Check if extracted data is available
    if "extracted_data" in st.session_state and st.session_state.extracted_data:
        extracted_data = st.session_state.extracted_data  # Retrieve JSON data

        # Display Matching Score
        overall_score = extracted_data.get("overall_score", 0)
        st.subheader(f"Matching Score: {overall_score}%")

        # Gauge Chart for Score Visualization
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_score,
            title={'text': "Resume Match Score", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {
                    'color': "#2ECC71" if overall_score >= 80 else "#F39C12" if overall_score >= 60 else "#E74C3C",
                    'thickness': 1
                },
                'bgcolor': "#F7F7F7"   
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

        # Key Insights
        st.subheader("🔍 Key Insights")
        st.write(f"✅ Your resume matches **{overall_score}%** with the job description.")

        if overall_score >= 80:
            st.success("✅ Your resume **strongly aligns** with the job requirements! 🎯")
        elif overall_score >= 60:
            st.warning("⚠️ Your resume **partially aligns** with the job description. Consider improving a few areas.")
        else:
            st.error("🚨 Your resume needs **significant improvements** to match the job description.")

        # Top Matching & Missing Skills 
        matching_skills = extracted_data.get("keyword_matching", [])
        if not isinstance(matching_skills, list):
            matching_skills = list(matching_skills) if matching_skills else []
        top_matching = matching_skills[:5]
        remaining_matching = matching_skills[5:]

        missing_skills = extracted_data.get("missing_keywords", [])
        if not isinstance(missing_skills, list):
            missing_skills = list(missing_skills) if missing_skills else []
        top_missing = missing_skills[:5]
        remaining_missing = missing_skills[5:]

        col_match, col_missing = st.columns([1, 1], gap="large")

        with col_match:
            st.markdown("<div style='margin-bottom: 20px;'><h2>✅ Top Matching Skills</h2></div>", unsafe_allow_html=True)
            if top_matching:
                st.success(", ".join(top_matching))
            else:
                st.warning("No matching skills found.")
            if remaining_matching:
                with st.expander(f"🔽 View all matched skills ({len(matching_skills)})"):
                    st.write(", ".join(remaining_matching))

        with col_missing:
            st.markdown("<div style='margin-bottom: 20px;'><h2>⚠️ Top Missing Skills</h2></div>", unsafe_allow_html=True)
            if top_missing:
                st.error(", ".join(top_missing))
            else:
                st.success("Great! No critical missing skills.")
            if remaining_missing:
                with st.expander(f"🔽 View all missing skills ({len(missing_skills)})"):
                    st.write(", ".join(remaining_missing))

        # Categorized Improvements
        st.subheader("📌 Categorized Improvements")

        suggestions = extracted_data.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = list(suggestions) if suggestions else []

        important_keys = {
            "Skills & Certifications": ["skill", "certification", "training"],
            "Experience & Work History": ["experience", "projects", "work history"],
            "Resume Formatting & Structure": ["format", "layout", "structure", "design"],
            "Education & Qualifications": ["education", "degree", "qualification"]
        }

        categorized_suggestions = {category: [] for category in important_keys.keys()}

        for suggestion in suggestions:
            for category, keywords in important_keys.items():
                if any(word in suggestion.lower() for word in keywords):
                    categorized_suggestions[category].append(f"🔹 {suggestion}")
                    break

        for category, items in categorized_suggestions.items():
            if items:
                with st.expander(f"📌 {category} ({len(items)})"):
                    for item in items:
                        st.markdown(item)

        if not any(categorized_suggestions.values()):
            st.success("No major improvements needed. Well done!")

        # High-Priority Suggestions Table
        st.write("### 🚀 High-Priority Improvement Suggestions")

        priority_data = []
        for suggestion in suggestions:
            if "experience" in suggestion.lower():
                priority = "High"
                color = "🔴"
            elif "skill" in suggestion.lower():
                priority = "Medium"
                color = "🟠"
            else:
                priority = "Low"
                color = "🟢"
            priority_data.append({
                "Improvement Suggestion": suggestion,
                "Priority": f"{color} {priority}"
            })

        priority_df = pd.DataFrame(priority_data)
        priority_df = priority_df.sort_values(by="Priority", ascending=False).head(5)
        st.dataframe(priority_df, use_container_width=True)

        # Navigation back button
        st.markdown("<br>", unsafe_allow_html=True)
        col_center = st.columns([1, 2, 1])[1]
        with col_center:
            if st.button("🔙 Back to Upload", use_container_width=True):
                st.session_state.page = "main"
                st.rerun()

    else:
        st.error("No extracted data available. Please upload a resume first.")

# Main Page: Resume Upload & Job Description
if st.session_state.page == "main":
    show_project_title()

    col1, col2 = st.columns([1, 1], gap="medium")

    # Resume Upload
    with col1:
        if "resume_uploaded" not in st.session_state:
            st.session_state.resume_uploaded = False
            st.session_state.uploaded_file = None

        if not st.session_state.resume_uploaded:
            st.subheader("Upload Resume")
            uploaded_file = st.file_uploader("Upload your PDF Resume", type=["pdf"])
            if uploaded_file is not None:
                file_path = save_uploaded_file(uploaded_file)
                st.session_state.resume_uploaded = True
                st.session_state.uploaded_file = uploaded_file
                st.session_state.file_path = file_path
                st.rerun()

        if st.session_state.resume_uploaded and st.session_state.uploaded_file:
            def get_pdf_base64(file_path):
                with open(file_path, "rb") as file:
                    base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                return f"data:application/pdf;base64,{base64_pdf}"

            pdf_data = get_pdf_base64(st.session_state.file_path)
            st.subheader("Uploaded Resume")
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            col3, col4 = st.columns([10, 1])
            with col3:
                st.markdown(
                    f'<iframe src="{pdf_data}" width="100%" height="400" style="border: none; margin-top: 15px;"></iframe>',
                    unsafe_allow_html=True,
                )
            with col4:
                if st.button("❌", key="remove_resume", help="Remove Resume", use_container_width=True):
                    remove_resume()

    # Job Description
    with col2:
        st.subheader("Enter Job Description")
        job_description = st.text_area("Paste the job description here", height=400)

    is_analyze_enabled = bool(job_description.strip()) and st.session_state.resume_uploaded

    # Analyse Resume Button
    st.markdown("<br>", unsafe_allow_html=True)
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        if st.button("🔍 Analyse Resume", use_container_width=True, disabled=not is_analyze_enabled):
            if is_analyze_enabled:
                loading_placeholder = show_loading_screen()
                try:
                    st.session_state.page = "analytics"
                    file_path = st.session_state.file_path
                    image_paths = pdf_to_jpg(file_path)
                    extracted_text = []

                    prompt = "Extract the text present in the image, and provide the result in JSON format."
                    for img_path in image_paths:
                        result = process_image(file_path=img_path, prompt=prompt, type="image")
                        extracted_text.append(result)

                    final_prompt = f"""
                    You are an AI-powered Resume Analyzer Assistant. Analyse this resume vs job description:
                    Job Description: {job_description}
                    Extracted Text: {extracted_text}
                    Return JSON: overall_score, keyword_matching, missing_keywords, suggestions, important_keys
                    """
                    final_result = process_image(file_path=extracted_text, prompt=final_prompt, type="text")
                    st.session_state.extracted_data = final_result
                finally:
                    loading_placeholder.empty()
                st.rerun()

# Show Analytics Page
elif st.session_state.page == "analytics":
    show_analytics()
