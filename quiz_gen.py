from langchain_google_vertexai import ChatVertexAI
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
import os
import json
from prompt import column_selection_prompt, quiz_level2_simple_prompt, quiz_recommendation_mapping_prompt, product_reasoning_prompt, important_columns_selection_prompt
import tempfile
import streamlit as st

from google.oauth2 import service_account
import vertexai

def get_configured_llm():
    """Get LLM with proper credentials"""
    
    # Get credentials from environment (set by your setup function)
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-vertex-ai-app")
    
    if credentials_path:
        # Load credentials from the temp file created by setup
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/vertex-ai'
            ]
        )
        
        return ChatVertexAI(
            model="gemini-2.5-flash",  # Use stable model
            temperature=0.5,
            max_tokens=None,
            max_retries=3,
            project=project_id,
            location="us-central1",
            credentials=credentials  # This is the key!
        )
    else:
        # Fallback to default credentials (for local development)
        return ChatVertexAI(
            model="gemini-2.5-flash",
            temperature=0.5,
            max_tokens=None,
            max_retries=3,
            project=project_id,
            location="us-central1"
        )

# Use this instead of global llm variable
llm = get_configured_llm()



def relevent_columns(column_names, industry, dataset):
    """
    Get relevant columns for any industry and dataset
    
    Parameters:
    column_names: List of column names from the dataset
    industry: Industry type (configurable)
    dataset: The actual pandas DataFrame (configurable)
    """
    column_selection_prompt_templete = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                column_selection_prompt,
            ),
            ("human", f"{column_names}"),
        ]
    )
    chain = column_selection_prompt_templete | llm

    # Use the provided dataset instead of hardcoded one
    product_map = {}
    for col in list(dataset.columns):
        product_map[col] = len(dataset[col].unique())

    generated_columns = chain.invoke(
        {
            "industry": f"{industry}",
            "column_names": ",".join([f"{k}:{v}" for k, v in product_map.items()])
        }
    )

    generated_columns = generated_columns.content
    generated_columns = json.loads(generated_columns[generated_columns.index("{") : generated_columns.rindex("}") + 1])
    
    # Use provided dataset instead of hardcoded one
    generated_columns_dataset = dataset[generated_columns["columns"]]
    generated_columns_with_unique_labels = {}

    for column in generated_columns["columns"]:
        print(column)
        generated_columns_with_unique_labels[column] = list(generated_columns_dataset[column].unique())

    return generated_columns_with_unique_labels

def get_level_quizes(generated_columns_with_unique_labels, quiz_1_res, company_name):
    """
    Generate Level 2 quiz questions
    
    Parameters:
    generated_columns_with_unique_labels: Dictionary of relevant columns and their unique values
    quiz_1_res: Level 1 quiz results
    company_name: Brand/company name (configurable)
    """
    level_two_quiz_prep_prompt_templete = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                quiz_level2_simple_prompt,
            ),
            ("human", "Catalog Information:- {catalog_info} Customer Profile {quiz_one_res}"),
        ]
    )

    chain = level_two_quiz_prep_prompt_templete | llm

    generated_questions = chain.invoke(
        {
            "company_name": company_name,  # Now configurable
            "catalog_info": ",".join([f"{k}: {v}" for k, v in generated_columns_with_unique_labels.items()]),
            "quiz_one_res": quiz_1_res
        })

    generated_questions = generated_questions.content
    generated_questions = json.loads(generated_questions[generated_questions.index("{") : generated_questions.rindex("}") + 1])

    return generated_questions

def rank_all_recommendations(df, recommendation_conditions):
    """
    Rank ALL products by how well they match conditions
    No products are filtered out - just ranked by match quality
    """
    
    df_ranked = df.copy()
    df_ranked['must_have_score'] = 0
    df_ranked['preferred_score'] = 0
    df_ranked['avoid_penalty'] = 0
    
    # Score MUST-HAVE conditions (higher weight)
    for cond in recommendation_conditions.get('must_have_conditions', []):
        col = cond['column_name']
        val = cond['value']
        condition_type = cond['condition']
        
        if col not in df.columns:
            continue
            
        # Handle NaN values safely
        col_series = df[col].fillna('')
        
        if condition_type == 'contains':
            matches = col_series.astype(str).str.contains(val, case=False, na=False)
        elif condition_type == 'equals':
            matches = (col_series.astype(str).str.lower() == str(val).lower())
        elif condition_type == 'not_contains':
            matches = ~col_series.astype(str).str.contains(val, case=False, na=False)
        elif condition_type == 'not_equals':
            matches = (col_series.astype(str).str.lower() != str(val).lower())
        else:
            matches = pd.Series([False] * len(df))
        
        df_ranked['must_have_score'] += matches.astype(int)
    
    # Score PREFERRED conditions (medium weight)
    for cond in recommendation_conditions.get('preferred_conditions', []):
        col = cond['column_name']
        val = cond['value']
        condition_type = cond['condition']
        
        if col not in df.columns:
            continue
            
        col_series = df[col].fillna('')
        
        if condition_type == 'contains':
            matches = col_series.astype(str).str.contains(val, case=False, na=False)
        elif condition_type == 'equals':
            matches = (col_series.astype(str).str.lower() == str(val).lower())
        else:
            matches = pd.Series([False] * len(df))
        
        df_ranked['preferred_score'] += matches.astype(int)
    
    # Apply AVOID penalties (negative scoring)
    for cond in recommendation_conditions.get('avoid_conditions', []):
        col = cond['column_name']
        val = cond['value']
        
        if col not in df.columns:
            continue
            
        col_series = df[col].fillna('')
        
        # Initialize violations to prevent UnboundLocalError
        violations = pd.Series([False] * len(df))
        
        if cond['condition'] == 'not_contains':
            violations = col_series.astype(str).str.contains(val, case=False, na=False)
        elif cond['condition'] == 'not_equals':
            violations = (col_series.astype(str).str.lower() == str(val).lower())
        
        df_ranked['avoid_penalty'] += violations.astype(int)
    
    # Calculate final ranking score
    # Must-have: 3 points each, Preferred: 1 point each, Avoid: -2 points each
    df_ranked['final_score'] = (
        df_ranked['must_have_score'] * 3 + 
        df_ranked['preferred_score'] * 1 + 
        df_ranked['avoid_penalty'] * -2
    )
    
    # Add match percentage for transparency
    total_conditions = (
        len(recommendation_conditions.get('must_have_conditions', [])) + 
        len(recommendation_conditions.get('preferred_conditions', []))
    )
    
    if total_conditions > 0:
        df_ranked['match_percentage'] = (
            (df_ranked['must_have_score'] + df_ranked['preferred_score']) / total_conditions * 100
        ).round(1)
    else:
        df_ranked['match_percentage'] = 0
    
    # Sort by match_percentage FIRST, then by final_score (both descending)
    df_ranked = df_ranked.sort_values(['match_percentage', 'final_score'], ascending=[False, False])
    
    return df_ranked

def get_recommendation(quiz_1_res, quiz_2_res, generated_columns_with_unique_labels, company_name):
    """
    Generate product recommendations based on quiz results
    
    Parameters:
    quiz_1_res: Level 1 quiz results
    quiz_2_res: Level 2 quiz results
    generated_columns_with_unique_labels: Relevant columns and values
    company_name: Brand/company name (configurable)
    """
    quiz_recommendation_mapping_prompt_templete = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            quiz_recommendation_mapping_prompt,
        ),
        ("human", "Level 1 Quiz Results{quiz_1_res} Level 2 Quiz Results{quiz_2_res} Product catalog:- {catalog_info}"),
        ]
    )

    chain = quiz_recommendation_mapping_prompt_templete | llm

    generated_rec = chain.invoke(
    {
        "company_name": company_name,  # Now configurable
        "catalog_info": ",".join([f"{k}: {v}" for k, v in generated_columns_with_unique_labels.items()]),
        "quiz_1_res": quiz_1_res,
        "quiz_2_res": quiz_2_res
    })
    
    generated_rec = generated_rec.content
    generated_rec = json.loads(generated_rec[generated_rec.index("{") : generated_rec.rindex("}") + 1])

    return generated_rec

def show_top_recs(df_ranked, n=3):
    """
    Show top recommendations with dynamically selected important columns
    """
    from prompt import important_columns_selection_prompt
    
    # Try AI selection
    try:
        important_columns_prompt_template = ChatPromptTemplate.from_messages([
            ("system", important_columns_selection_prompt),
            ("human", "Select the most important columns for customers.")
        ])
        
        chain = important_columns_prompt_template | llm
        
        # Get column info (excluding scoring columns from AI analysis)
        column_info = {col: len(df_ranked[col].unique()) 
                      for col in df_ranked.columns 
                      if col not in ['match_percentage', 'final_score']}
        
        response = chain.invoke({"column_info": str(column_info)})
        response_content = response.content
        response_json = json.loads(response_content[response_content.index("{") : response_content.rindex("}") + 1])
        
        # Get AI selected columns + scoring columns
        ai_selected = response_json.get("important_columns", [])
        display_cols = ai_selected + ['match_percentage', 'final_score']
        
        # Filter to existing columns
        display_cols = [c for c in display_cols if c in df_ranked.columns]
        
        print(f"AI selected columns: {display_cols}")
        
    except Exception as e:
        print(f"AI selection failed: {e}, using all available columns")
        # Fallback: just use all columns (truly dynamic, no hardcoding)
        display_cols = list(df_ranked.columns)
    
    return df_ranked[display_cols].head(n).reset_index(drop=True)

def generate_product_reasoning_ai(quiz_1_res, quiz_2_res, product_row, company_name=""):
    """
    Generate simple 3-line reasoning for product recommendation
    
    Parameters:
    quiz_1_res: Level 1 quiz results
    quiz_2_res: Level 2 quiz results
    product_row: Single product information
    company_name: Brand name (configurable)
    """
    reasoning_prompt_template = ChatPromptTemplate.from_messages([
        ("system", product_reasoning_prompt),
        ("human", "Generate 3-line reasoning for this product recommendation from {company_name}.")
    ])
    
    chain = reasoning_prompt_template | llm
    
    try:
        # Handle different possible column names for product information
        product_name = product_row.get('Name') or product_row.get('Product_Name') or product_row.get('Title', 'This product')
        suitable_for = product_row.get('SuitableFor') or product_row.get('Suitable_For', '')
        concern = product_row.get('Concern') or product_row.get('Concerns', '')
        key_ingredients = product_row.get('Key_Ingredients') or product_row.get('Ingredients', '')
        free_from = product_row.get('Free_From') or product_row.get('Free', '')
        
        response = chain.invoke({
            "quiz_1_results": str(quiz_1_res),
            "quiz_2_results": str(quiz_2_res),
            "product_name": product_name,
            "suitable_for": suitable_for,
            "concern": concern,
            "key_ingredients": key_ingredients,
            "free_from": free_from,
            "company_name": company_name
        })
        
        # Get the response and ensure exactly 3 lines
        reasoning = response.content

        response_content = response.content
        response_json = json.loads(response_content[response_content.index("{") : response_content.rindex("}") + 1])

        return response_json
            
    except Exception as e:
        return f"This product from {company_name} matches your specific needs and preferences. The formulation addresses your main concerns effectively and safely. It's designed to work well with your routine and experience level."