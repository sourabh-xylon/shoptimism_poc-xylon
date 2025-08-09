from langchain_core.prompts import ChatPromptTemplate
import json
from prompts.product_reasoning import product_reasoning_prompt
from llm.congifure_llm import llm


"***Below Function can be impooved by letting ai slect the important columns dynamically***"

def generate_product_reasoning_ai(quiz_1_res: str, quiz_2_res: str, product_row: dict, company_name: str):

    """
    Generate simple 3-line reasoning for product recommendation
    
    Parameters:
    quiz_1_res: Level 1 quiz results
    quiz_2_res: Level 2 quiz results
    product_row: Single product information
    company_name: Brand name 
    """
    try:
        reasoning_prompt_template = ChatPromptTemplate.from_messages([
            ("system", product_reasoning_prompt),
            ("human", "Generate 3-line reasoning for this product recommendation from {company_name}.")
        ])
        
        chain = reasoning_prompt_template | llm
    
    
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


        response_content = response.content
        response_json = json.loads(response_content[response_content.index("{") : response_content.rindex("}") + 1])

        return response_json
            
    except Exception as e:
        return {"message": "Error while generating product reasoning", "error": str(e)}