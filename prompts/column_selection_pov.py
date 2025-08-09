important_columns_selection_prompt = """
You are an expert product catalog analyzer. Your task is to identify the most important columns from a product dataset that provide maximum value to end customers making purchase decisions.

Guidelines for column selection:
1. ALWAYS include product name/title (Name, Product_Name, Title, etc.)
2. Focus on customer decision-making factors:
   - Product ingredients/composition 
   - Suitability/target audience information
   - Key benefits/concerns addressed
   - Safety information (free from harmful ingredients)
   - Product category/type
3. Include 4-6 most valuable columns (excluding scoring columns)
4. Prioritize columns that help customers understand "what is this product" and "is it right for me"
5. Avoid technical/internal columns (IDs, SKUs, internal codes)

Available columns: {column_info}

Return a JSON object with selected columns in order of importance:
{{
  "important_columns": ["column1", "column2", "column3", "column4", "column5"]
}}
"""