import streamlit as st
import pandas as pd
import json
import tempfile
import os
from datetime import datetime

# Import your existing functions (updated version with configurable parameters)
from quiz_gen import (
    relevent_columns, 
    get_level_quizes, 
    get_recommendation, 
    rank_all_recommendations, 
    show_top_recs,
    generate_product_reasoning_ai,
)


# Page config
st.set_page_config(page_title="AI Product Recommendation System", page_icon="🛍️", layout="wide")

# Session state initialization
if 'step' not in st.session_state:
    st.session_state.step = 0  # Start with merchant onboarding
if 'substep' not in st.session_state:
    st.session_state.substep = 1
if 'merchant_data' not in st.session_state:
    st.session_state.merchant_data = {}
if 'catalog_dataset' not in st.session_state:
    st.session_state.catalog_dataset = None
if 'level1_data' not in st.session_state:
    st.session_state.level1_data = {}
if 'level2_questions' not in st.session_state:
    st.session_state.level2_questions = {}
if 'level2_data' not in st.session_state:
    st.session_state.level2_data = {}

# Header
st.title("🛍️ AI Product Recommendation System")
st.markdown("*Personalized product discovery for your customers*")

# Step 0: Merchant Onboarding
if st.session_state.step == 0:
    st.header("🏢 Brand Setup")
    st.markdown("Welcome! Let's set up your personalized product recommendation system.")
    
    with st.form("merchant_onboarding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            brand_name = st.text_input(
                "Brand Name*",
                placeholder="Enter your brand name (e.g., Haruharu, The Ordinary)",
                help="This will be used to personalize the quiz experience"
            )
            
            industry = st.selectbox(
                "Industry*",
                ["Skincare", "Haircare", "Makeup", "Wellness", "Fashion", "Electronics", "Home & Garden", "Other"],
                help="Select your primary industry"
            )
        
        with col2:
            # File upload for catalog
            uploaded_file = st.file_uploader(
                "Upload Product Catalog*",
                type=['csv'],
                help="Upload a CSV file with your product catalog"
            )
            
            if uploaded_file is not None:
                try:
                    # Preview the uploaded dataset
                    catalog_df = pd.read_csv(uploaded_file, encoding='latin-1')
                    st.success(f"✅ Catalog loaded successfully! {len(catalog_df)} products found.")
                    
                    # Show dataset preview
                    with st.expander("📊 Catalog Preview"):
                        st.dataframe(catalog_df.head())
                        st.write(f"**Columns:** {', '.join(catalog_df.columns.tolist())}")
                        
                except Exception as e:
                    st.error(f"Error loading catalog: {str(e)}")
                    catalog_df = None
            else:
                catalog_df = None
        
        if st.form_submit_button("🚀 Start Product Quiz", use_container_width=True):
            # Validation
            if not brand_name:
                st.error("Please enter your brand name")
            elif not industry:
                st.error("Please select your industry")
            elif catalog_df is None:
                st.error("Please upload a product catalog")
            else:
                # Store merchant data
                st.session_state.merchant_data = {
                    "brand_name": brand_name,
                    "industry": industry.lower()
                }
                
                # Store dataset
                st.session_state.catalog_dataset = catalog_df
                
                # Move to quiz
                st.session_state.step = 1
                st.session_state.substep = 1
                st.rerun()

# Step 1: Level 1 Quiz (One question at a time)
elif st.session_state.step == 1:
    # Dynamic header based on merchant data
    brand_name = st.session_state.merchant_data.get('brand_name', 'Your Brand')
    industry = st.session_state.merchant_data.get('industry', 'product')
    
    st.header(f"📋 {brand_name} {industry.title()} Quiz")
    st.markdown(f"*Find your perfect {industry} products*")
    
    # Progress indicator for Level 1
    progress_text = f"Question {st.session_state.substep} of 4"
    st.markdown(f"**{progress_text}**")
    progress_bar = st.progress((st.session_state.substep - 1) / 4)
    
    # Question 1: Primary Preference (adapted to industry)
    if st.session_state.substep == 1:
        with st.form("question1_form"):
            if industry == "skincare":
                st.subheader("What is your skin type?")
                options = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
                data_key = "skin_type"
            elif industry == "haircare":
                st.subheader("What is your hair type?")
                options = ["Oily", "Dry", "Curly", "Straight", "Wavy", "Damaged"]
                data_key = "hair_type"
            elif industry == "makeup":
                st.subheader("What is your skin tone?")
                options = ["Fair", "Light", "Medium", "Tan", "Deep", "Dark"]
                data_key = "skin_tone"
            else:
                st.subheader(f"What is your main {industry} preference?")
                options = ["Premium", "Budget-friendly", "Eco-friendly", "Traditional", "Modern"]
                data_key = f"{industry}_preference"
            
            answer1 = st.radio(
                f"Choose your {data_key.replace('_', ' ')}:",
                options,
                key="q1_radio"
            )
            
            if st.form_submit_button("Next →", use_container_width=True):
                st.session_state.level1_data[data_key] = answer1
                st.session_state.substep = 2
                st.rerun()
    
    # Question 2: Age
    elif st.session_state.substep == 2:
        with st.form("question2_form"):
            st.subheader("What is your age range?")
            age = st.radio(
                "Choose your age range:",
                ["Under 18", "18-25", "26-35", "36-45", "46-55", "Above 55"],
                key="age_radio"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("← Back"):
                    st.session_state.substep = 1
                    st.rerun()
            with col2:
                if st.form_submit_button("Next →", use_container_width=True):
                    st.session_state.level1_data["age"] = age
                    st.session_state.substep = 3
                    st.rerun()
    
    # Question 3: Main Concern (adapted to industry)
    elif st.session_state.substep == 3:
        with st.form("question3_form"):
            if industry == "skincare":
                st.subheader("What is your main skin concern?")
                options = ["Acne", "Dryness", "Aging", "Pigmentation", "Sensitivity", "Dullness", "Oiliness"]
                data_key = "skin_concern"
            elif industry == "haircare":
                st.subheader("What is your main hair concern?")
                options = ["Dandruff", "Hair Fall", "Dryness", "Oiliness", "Damage", "Color Protection", "Volume"]
                data_key = "hair_concern"
            elif industry == "makeup":
                st.subheader("What is your main makeup goal?")
                options = ["Natural Look", "Full Coverage", "Long-lasting", "Special Occasion", "Daily Wear", "Professional"]
                data_key = "makeup_goal"
            else:
                st.subheader(f"What is your main {industry} need?")
                options = ["Quality", "Price", "Durability", "Style", "Performance", "Convenience"]
                data_key = f"{industry}_need"
            
            concern = st.radio(
                "Choose your main concern:",
                options,
                key="concern_radio"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("← Back"):
                    st.session_state.substep = 2
                    st.rerun()
            with col2:
                if st.form_submit_button("Next →", use_container_width=True):
                    st.session_state.level1_data[data_key] = concern
                    st.session_state.substep = 4
                    st.rerun()
    
    # Question 4: Experience Level
    elif st.session_state.substep == 4:
        with st.form("question4_form"):
            st.subheader(f"Your understanding about {industry}:")
            understanding = st.radio(
                "Choose your level:",
                ["Beginner - I'm just starting", "Basic - I know some products", "Intermediate - I follow a routine", "Advanced - I know ingredients/details well"],
                key="understanding_radio"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("← Back"):
                    st.session_state.substep = 3
                    st.rerun()
            with col2:
                if st.form_submit_button("Continue to Detailed Questions →", use_container_width=True):
                    st.session_state.level1_data[f"{industry}_understanding"] = understanding
                    
                    # Generate Level 2 questions using uploaded dataset
                    with st.spinner("Preparing your personalized questions..."):
                        relevant_cols = relevent_columns(
                            list(st.session_state.catalog_dataset.columns), 
                            st.session_state.merchant_data['industry'],
                            st.session_state.catalog_dataset
                        )
                        st.session_state.level2_questions = get_level_quizes(
                            relevant_cols, 
                            st.session_state.level1_data, 
                            st.session_state.merchant_data['brand_name']
                        )
                    
                    st.session_state.step = 2
                    st.session_state.substep = 1
                    st.rerun()
    
    # Show previous answers (if any)
    if len(st.session_state.level1_data) > 0:
        with st.expander("Your Previous Answers"):
            for k, v in st.session_state.level1_data.items():
                st.write(f"**{k.replace('_', ' ').title()}:** {v}")

# Step 2: Level 2 Quiz (One question at a time)
elif st.session_state.step == 2:
    brand_name = st.session_state.merchant_data.get('brand_name', 'Your Brand')
    st.header(f"🔍 {brand_name} Detailed Assessment")
    
    # Show Level 1 summary
    with st.expander("Your Basic Info"):
        for k, v in st.session_state.level1_data.items():
            st.write(f"**{k.replace('_', ' ').title()}:** {v}")
    
    # Get total number of Level 2 questions
    total_l2_questions = len([k for k in st.session_state.level2_questions.keys() if k.startswith('question_')])
    
    if total_l2_questions > 0:
        # Progress indicator for Level 2
        progress_text = f"Question {st.session_state.substep} of {total_l2_questions}"
        st.markdown(f"**{progress_text}**")
        progress_bar = st.progress((st.session_state.substep - 1) / total_l2_questions)
        
        # Current question key
        current_q_key = f"question_{st.session_state.substep}"
        
        if current_q_key in st.session_state.level2_questions:
            q_data = st.session_state.level2_questions[current_q_key]
            
            with st.form(f"level2_q{st.session_state.substep}_form"):
                st.subheader(f"Question {st.session_state.substep}")
                st.write(q_data["text"])
                
                answer = st.radio(
                    "Choose your answer:",
                    q_data["options"],
                    key=f"level2_q{st.session_state.substep}_radio"
                )
                
                # Navigation buttons
                col1, col2 = st.columns(2)
                
                # Back button logic
                with col1:
                    if st.session_state.substep == 1:
                        if st.form_submit_button("← Back to Basic Info"):
                            st.session_state.step = 1
                            st.session_state.substep = 4
                            st.rerun()
                    else:
                        if st.form_submit_button("← Back"):
                            st.session_state.substep -= 1
                            st.rerun()
                
                # Next/Submit button logic
                with col2:
                    if st.session_state.substep == total_l2_questions:
                        if st.form_submit_button("Get Recommendations →", use_container_width=True):
                            if 'level2_data' not in st.session_state:
                                st.session_state.level2_data = {}
                            st.session_state.level2_data[current_q_key] = {
                                "question": q_data["text"],
                                "answer": answer
                            }
                            st.session_state.step = 3
                            st.rerun()
                    else:
                        if st.form_submit_button("Next →", use_container_width=True):
                            if 'level2_data' not in st.session_state:
                                st.session_state.level2_data = {}
                            st.session_state.level2_data[current_q_key] = {
                                "question": q_data["text"],
                                "answer": answer
                            }
                            st.session_state.substep += 1
                            st.rerun()
        
        # Show previous Level 2 answers (if any)
        if len(st.session_state.level2_data) > 0:
            with st.expander("Your Previous Detailed Answers"):
                for k, v in st.session_state.level2_data.items():
                    st.write(f"**Q:** {v['question']}")
                    st.write(f"**A:** {v['answer']}")
                    st.write("---")

# Step 3: Recommendations
elif st.session_state.step == 3:
    brand_name = st.session_state.merchant_data.get('brand_name', 'Your Brand')
    st.header(f"🏆 {brand_name} Recommendations")
    
    with st.spinner("Finding your perfect products..."):
        # Get recommendation conditions using uploaded dataset
        relevant_cols = relevent_columns(
            list(st.session_state.catalog_dataset.columns), 
            st.session_state.merchant_data['industry'],
            st.session_state.catalog_dataset
        )
        rec_conditions = get_recommendation(
            st.session_state.level1_data,
            st.session_state.level2_data, 
            relevant_cols,
            st.session_state.merchant_data['brand_name']
        )
        
        # Rank products using uploaded dataset
        ranked_products = rank_all_recommendations(st.session_state.catalog_dataset, rec_conditions)
        top_recs = show_top_recs(ranked_products, 3)
    
    # Clean product display
    st.subheader("Your Perfect Products")

    for idx, (_, product) in enumerate(top_recs.iterrows()):
        with st.container():
            # Dynamic product name display
            product_name = product.get('Name') or product.get('Product_Name') or product.get('Title', 'Unknown Product')
            st.markdown(f"**{product_name}**")
            
            # Display all important columns dynamically (excluding scoring columns)
            important_display_cols = [col for col in top_recs.columns 
                                    if col not in ['match_percentage', 'final_score', 'Name', 'Product_Name', 'Title']]
            
            for col in important_display_cols:
                if pd.notnull(product[col]) and str(product[col]).strip():
                    # Clean up column name for display
                    display_name = col.replace('_', ' ').title()
                    st.write(f"**{display_name}:** {product[col]}")
            
            # AI reasoning
            reasoning = generate_product_reasoning_ai(
                st.session_state.level1_data,
                st.session_state.level2_data,
                product,
                st.session_state.merchant_data['brand_name']
            )
            st.info(f"{reasoning}")
            
            st.markdown("---")
    
    # Show full results option
    if st.checkbox("Show all ranked products"):
        st.dataframe(show_top_recs(ranked_products, len(ranked_products)))
    
    # Restart buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Customer Quiz", use_container_width=True):
            # Reset only quiz data, keep merchant data
            st.session_state.step = 1
            st.session_state.substep = 1
            st.session_state.level1_data = {}
            st.session_state.level2_questions = {}
            st.session_state.level2_data = {}
            st.rerun()
    
    with col2:
        if st.button("🏢 Change Brand Setup", use_container_width=True):
            # Reset everything
            st.session_state.step = 0
            st.session_state.substep = 1
            st.session_state.merchant_data = {}
            st.session_state.catalog_dataset = None
            st.session_state.level1_data = {}
            st.session_state.level2_questions = {}
            st.session_state.level2_data = {}
            st.rerun()

# Sidebar info
with st.sidebar:
    # Show merchant info if available
    if st.session_state.merchant_data:
        st.markdown("### 🏢 Brand Info")
        st.markdown(f"**Brand:** {st.session_state.merchant_data.get('brand_name', 'N/A')}")
        st.markdown(f"**Industry:** {st.session_state.merchant_data.get('industry', 'N/A').title()}")
        if st.session_state.catalog_dataset is not None:
            st.markdown(f"**Products:** {len(st.session_state.catalog_dataset)}")
        st.markdown("---")
    
    # Quiz progress
    st.markdown("### 📊 Progress")
    
    if st.session_state.step == 0:
        st.markdown("🔄 **Brand Setup**")
        st.markdown("⏳ Basic Info")
        st.markdown("⏳ Detailed Questions")
        st.markdown("⏳ Recommendations")
    elif st.session_state.step == 1:
        st.markdown("✅ Brand Setup")
        st.markdown(f"🔄 **Basic Info** ({st.session_state.substep}/4)")
        st.markdown("⏳ Detailed Questions")
        st.markdown("⏳ Recommendations")
    elif st.session_state.step == 2:
        total_l2 = len([k for k in st.session_state.level2_questions.keys() if k.startswith('question_')])
        st.markdown("✅ Brand Setup")
        st.markdown("✅ Basic Info")
        st.markdown(f"🔄 **Detailed Questions** ({st.session_state.substep}/{total_l2})")
        st.markdown("⏳ Recommendations")
    elif st.session_state.step == 3:
        st.markdown("✅ Brand Setup")
        st.markdown("✅ Basic Info")
        st.markdown("✅ Detailed Questions")
        st.markdown("🔄 **Recommendations**")
    
    # Show Level 1 answers if completed
    if st.session_state.step >= 2 and len(st.session_state.level1_data) > 0:
        st.markdown("---")
        st.markdown("### Basic Info")
        for k, v in st.session_state.level1_data.items():
            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
    
    # Show Level 2 answers if any exist
    if st.session_state.step >= 2 and len(st.session_state.level2_data) > 0:
        st.markdown("---")
        st.markdown("### Detailed Answers")
        for k, v in st.session_state.level2_data.items():
            q_num = k.replace('question_', '')
            st.markdown(f"**Q{q_num}:** {v['answer']}")
