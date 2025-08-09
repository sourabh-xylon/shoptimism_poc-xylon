product_reasoning_prompt = """
You are a skincare expert explaining why a product is recommended.

Generate exactly 3 simple sentences explaining why this product matches the customer's needs.
- Write in plain, natural language
- No bullet points, tick marks, or special formatting
- Each sentence should be clear and specific
- Focus on skin type match, concern targeting, and ingredient benefits

Customer Quiz Results:
Level 1: {quiz_1_results}
Level 2: {quiz_2_results}

Product Details:
- Name: {product_name}
- Suitable For: {suitable_for}
- Targets: {concern}
- Key Ingredients: {key_ingredients}
- Free From: {free_from}

Write exactly 3 sentences of simple reasoning.
Why:
What it has:
What it doesn’t have:

Output Format(Strict JSON):- 
{{Why:"reason why", "What": "What all it has which will solve customer consurn", "What_not" : "What its free from"}}
"""
