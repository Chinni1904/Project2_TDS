import pandas as pd
import json
import requests
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

def load_dataset(file_path):
    """Loads a dataset from a CSV file."""
    try:
        df = pd.read_csv(file_path, encoding='latin1')
        print(f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        raise RuntimeError(f"Error loading dataset: {e}")

def visualize_data(df, output_dir):
    """Generates and saves a correlation heatmap."""
    try:
        correlation = df.corr(numeric_only=True)
        plt.figure(figsize=(12, 8))
        sns.heatmap(correlation, annot=True, cmap='coolwarm')

        # Save the plot as a PNG file with dataset name
        heatmap_filename = os.path.join(output_dir, f"{output_dir}.png")
        plt.savefig(heatmap_filename)
        plt.close()

        print(f"Heatmap saved as {heatmap_filename}.")
        return heatmap_filename
    except Exception as e:
        raise RuntimeError(f"Error generating heatmap: {e}")
    

def analyze_data(df):
    """Performs basic analysis on the dataset."""
    try:
        analysis = {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "column_types": df.dtypes.astype(str).to_dict(),
            "summary_statistics": df.describe(include='all').to_dict()
        }
        print("Data analysis completed.")
        return analysis
    except Exception as e:
        raise RuntimeError(f"Error during data analysis: {e}")

def llm_summary(analysis):
    """Generates a summary of the dataset using an LLM."""
    load_dotenv()
    api_key = os.getenv("AIPROXY_TOKEN")

    if not api_key:
        raise Exception("API key not found. Please set AIPROXY_TOKEN in your .env file.")

    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = f"""
    Analyze the following dataset metadata and provide insights:
    {json.dumps(analysis, indent=2)}
    """

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

def save_to_readme(heatmap_filename, analysis, summary, output_dir):
    """Saves analysis results and summary to a README.md file."""
    os.makedirs(output_dir, exist_ok=True)

    readme_content = f"""
# Data Analysis Report

## Correlation Heatmap
![Heatmap](./{os.path.basename(heatmap_filename)})

## Analysis Results
**Number of Rows:** {analysis["num_rows"]}  
**Number of Columns:** {analysis["num_columns"]}  

### Missing Values:
```json
{json.dumps(analysis["missing_values"], indent=2)}
```

### Column Types:
```json
{json.dumps(analysis["column_types"], indent=2)}
```

### Summary Statistics:
```json
{json.dumps(analysis["summary_statistics"], indent=2)}
```

## Summary
{summary}
"""

    readme_filename = os.path.join(output_dir, "README.md")

    with open(readme_filename, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Results saved in {readme_filename}")

def main():
    parser = argparse.ArgumentParser(description="Automated data analysis and reporting.")
    parser.add_argument("file_path", help="Path to the CSV file to analyze.")
    args = parser.parse_args()

    file_path = args.file_path

    # Get dataset name without extension
    df = os.path.splitext(os.path.basename(file_path))[0]

    # Create subfolder for the dataset in the current directory
    dataset_folder = os.path.join(os.getcwd(), df)

    # Ensure the folder exists
    os.makedirs(dataset_folder, exist_ok=True)

    # Step 1: Load the dataset
    df = load_dataset(file_path)

    # Step 2: Visualize the data
    heatmap_filename = visualize_data(df, dataset_folder)

    # Step 3: Analyze the data
    analysis = analyze_data(df)

    # Step 4: Generate a summary using LLM
    summary = llm_summary(analysis)

    # Step 5: Save everything to README.md in the dataset's folder
    save_to_readme(heatmap_filename, analysis, summary, dataset_folder)

if __name__ == "__main__":
    main()