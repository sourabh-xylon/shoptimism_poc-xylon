import pandas as pd

def rank_all_recommendations(df: pd, recommendation_conditions: dict):
    
    """
    Rank ALL products by how well they match conditions
    No products are filtered out - just ranked by match quality
    """

    try:
    
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
    
    except Exception as e:
        return {"message": "Error while ranking recommendations", "error": str(e)}