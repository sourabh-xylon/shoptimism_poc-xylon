from langchain_core.prompts import ChatPromptTemplate
import json
from prompts.recommendation_query_building import quiz_recommendation_mapping_prompt
from llm.congifure_llm import llm

def get_recommendation(quiz_1_res: str, quiz_2_res: str, generated_columns_with_unique_labels: dict, company_name: str):

    """
    Generate product recommendations based on quiz results
    
    Parameters:
    quiz_1_res: Level 1 quiz results
    quiz_2_res: Level 2 quiz results
    generated_columns_with_unique_labels: Relevant columns and values
    company_name: Brand/company name (configurable)

    """
    try:

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
            "company_name": company_name,  
            "catalog_info": ",".join([f"{k}: {v}" for k, v in generated_columns_with_unique_labels.items()]),
            "quiz_1_res": quiz_1_res,
            "quiz_2_res": quiz_2_res
        })
        
        generated_rec = generated_rec.content
        generated_rec = json.loads(generated_rec[generated_rec.index("{") : generated_rec.rindex("}") + 1])

        return generated_rec
    
    except Exception as e:
        return {"message": "Error while getting recommendations", "error": str(e)}