from langchain_core.prompts import ChatPromptTemplate
import json
import pandas as pd
from prompts.column_selection_pov import important_columns_selection_prompt
from llm.congifure_llm import llm

def show_top_recs(df_ranked: pd.DataFrame, n:int = 3):

    """
    Show top recommendations with dynamically selected important columns
    """
    
    
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
        
       

        return df_ranked[display_cols].head(n).reset_index(drop=True)
        
    except Exception as e:
        
        return {"message": "Error while getting top recommendations", "error": str(e)}
    
    

