from langchain_core.prompts import ChatPromptTemplate
import json
from prompts.column_selection import column_selection_prompt 
from llm.congifure_llm import llm
from typing import List
import pandas as pd



def relevent_columns(column_names: List, industry: str, dataset: pd.DataFrame):
    """
    Get relevant columns for any industry and dataset
    
    Parameters:
    column_names: List of column names from the dataset
    industry: Industry type 
    dataset: The actual pandas DataFrame 
    """
    try:

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
    
    except Exception as e:

        return {"message":"Error while getting relevant columns", "Error": str(e)}
