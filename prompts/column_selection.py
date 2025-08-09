column_selection_prompt = """
You are a domain expert building a smart recommendation system in the {industry} industry.
Below is a list of product database columns. Your job is to select only the columns that would help generate meaningful questions about a customer’s pain points, lifestyle, or concerns.

Include columns that relate to:
- The customer's problem or goal
- Sensitivities 
- Relate to compatibility, environment, or lifestyle

Exclude columns that are:
- Metadata (IDs, links, names, images)
- Internal or display-only fields
- Direct Product Information (Brand, Price)
- Unstructured or non-specific data (Reviews, Description, Keywords)
- Internal, inventory, or marketing-related

Output(Strict JSON):- 
{{"columns" : [List of columns spearted by comma]}}
"""
