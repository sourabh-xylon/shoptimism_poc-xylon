from langchain_core.prompts import ChatPromptTemplate
import json
from prompts.level_two_quiz_prepration import quiz_level2_simple_prompt
from llm.congifure_llm import llm

def get_level_quizes(generated_columns_with_unique_labels: dict, quiz_1_res: str, company_name: str):

    """
    Generate Level 2 quiz questions
    
    Parameters:
    generated_columns_with_unique_labels: Dictionary of relevant columns and their unique values
    quiz_1_res: Level 1 quiz results
    company_name: Brand/company name 

    """
    try:

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
                "company_name": company_name, 
                "catalog_info": ",".join([f"{k}: {v}" for k, v in generated_columns_with_unique_labels.items()]),
                "quiz_one_res": quiz_1_res
            })

        generated_questions = generated_questions.content
        generated_questions = json.loads(generated_questions[generated_questions.index("{") : generated_questions.rindex("}") + 1])

        return generated_questions
    except Exception as e:
        return {"message": "Error while generating level 2 quiz questions", "error": str(e)}