import subprocess
import sys
import importlib
import os
#from dateutil.parser import parse

# Ensure pip is installed and updated
def ensure_pip():
    try:
        import pip
        print("'pip' is already available.")
    except ImportError:
        print("'pip' not found. Installing pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            print("'pip' has been installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install pip: {e}")
            sys.exit(1)

# Function to check and install a package
def install_and_import(package_name):
    try:
        importlib.import_module(package_name)
        print(f"'{package_name}' is already installed.")
    except ImportError:
        print(f"'{package_name}' not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"'{package_name}' has been installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install '{package_name}': {e}")
            sys.exit(1)

# List of required packages with aliases
packages_with_aliases = {
    "pandas": "pd",
    "matplotlib.pyplot": "plt",
    "seaborn": "sns",
    "openai": None,
    "numpy": "np",
    "tabulate": "tabulate"
}

# Ensure pip is installed
ensure_pip()

# Check and install each package
for package in packages_with_aliases.keys():
    install_and_import(package.split('.')[0])  # Handle submodules

# Import the packages with aliases
for package, alias in packages_with_aliases.items():
    try:
        module = importlib.import_module(package)
        if alias:
            globals()[alias] = module
        else:
            globals()[package] = module
    except ModuleNotFoundError as e:
        print(f"Error importing '{package}': {e}")
        sys.exit(1)

# Example usage to confirm everything is working
print("All packages have been successfully installed and imported!")

# Retrieve the Bearer token from the environment variable
openai.api_key = os.getenv("AIPROXY_TOKEN")
if not openai.api_key:
    raise ValueError("Environment variable AIPROXY_TOKEN is not set.")

url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openai.api_key}",
    "Content-Type": "application/json"
}

# Step 1: Analyze Dataset
def analyze_dataset(file_path):
    data = pd.read_csv(file_path,encoding='ISO-8859-1')

    # Descriptive Statistics
    desc_stats = data.describe(include='all').transpose()

    # Correlation Matrix
    numeric_data = data.select_dtypes(include=['number'])
    corr_matrix = numeric_data.corr() if not numeric_data.empty else None

    # Missing Values
    missing_values = data.isnull().sum()

    # Data Summary
    summary = {
        "num_rows": len(data),
        "num_columns": len(data.columns),
        "columns": data.dtypes.to_dict(),
        "missing_values": missing_values.to_dict(),
        "desc_stats_summary": desc_stats[['mean', 'std', 'min', '25%', '50%', '75%', 'max']] if not desc_stats.empty else None,
        "corr_matrix_summary": corr_matrix.describe() if corr_matrix is not None else None,
    }

    return data, summary

# Step 2: Enhanced Visualizations
def visualize_data(data, summary):
    visualizations = []
    output_dir = "./"  # Save charts in the current directory

    # 1. Numeric Column Distribution
    numeric_columns = data.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
         for col in numeric_columns:
            if len(visualizations) >= 2:
                break  # Limit visuals 
            plt.figure(figsize=(10, 6))
            sns.histplot(data[col].dropna(), kde=True, color='skyblue', alpha=0.7)
            plt.title(f"Distribution of {col}", fontsize=16)
            plt.xlabel(col, fontsize=14)
            plt.ylabel("Frequency", fontsize=14)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plot_path = os.path.join(output_dir, f"{col}_distribution.png")
            plt.savefig(plot_path, dpi=100) #adjust resolution
            visualizations.append(plot_path)
            plt.close()

    # 2. Correlation Heatmap
    if summary["corr_matrix_summary"] is not None and len(visualizations) < 5:
        plt.figure(figsize=(12, 8))
        sns.heatmap(
            summary["corr_matrix_summary"], 
            annot=True, 
            fmt=".2f", 
            cmap="coolwarm", 
            cbar_kws={"shrink": 0.8}
        )
        plt.title("Correlation Heatmap", fontsize=16)
        plt.xticks(fontsize=12, rotation=45)
        plt.yticks(fontsize=12)
        plot_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(plot_path, dpi=100) #adjust resolution)
        visualizations.append(plot_path)
        plt.close()

    # 3. Top 2 Categorical Columns Visualization
    categorical_columns = data.select_dtypes(include=['object']).columns
    non_date_categoricals = [
        col for col in categorical_columns if not is_date_column(data[col])
    ]
    if len(visualizations) <= 5 and len(categorical_columns) > 0:
        # Rank categorical columns by their unique value count
        unique_counts = {col: data[col].nunique() for col in non_date_categoricals}
        top_categorical_cols = sorted(unique_counts, key=unique_counts.get, reverse=True)[:2]

        for col in top_categorical_cols:
            top_categories = data[col].value_counts().head(10)
            sns.barplot(x=top_categories.index, y=top_categories.values, palette="viridis")
            plt.title(f"Top 10 Categories in {col}", fontsize=14)
            plt.xlabel(col, fontsize=12)
            plt.ylabel("Count", fontsize=12)
            plt.xticks(rotation=45, ha='right', fontsize=10)
            for i, val in enumerate(top_categories.values):
                plt.text(i, val, f"{val}", ha='center', va='bottom', fontsize=10)
            plot_path = os.path.join(output_dir, f"{col}_top_categories.png")
            plt.savefig(plot_path, dpi=100)  # Adjust dpi for 512x512 resolution
            visualizations.append(plot_path)
            plt.close()


    return visualizations

'''def is_date_column(series):
    """
    Determines if a column is likely to represent dates.
    Tries to parse a sample of the series to confirm if it's date-like.
    """
    if series.dtype == 'datetime64[ns]':  # Already datetime
        return True
    if series.dtype == 'object':  # Object type; check for dates
        try:
            # Sample a small portion of the column to test for date parsing
            sample = series.dropna().sample(min(10, len(series.dropna())))
            for value in sample:
                parse(value, fuzzy=False)  # Attempts strict date parsing
            return True
        except (ValueError, TypeError):  # If parsing fails, it's not a date
            return False
    return False'''


# Sanitization Function
def sanitize_summary(summary):
    """Ensure summary content is safe and does not contain injection patterns."""
    sanitized = {}
    for key, value in summary.items():
        if isinstance(value, dict):
            sanitized[key] = {k: str(v).replace('\n', ' ').replace('\r', '') for k, v in value.items()}
        elif isinstance(value, pd.DataFrame):
            sanitized[key] = value.head(5).to_markdown()  # Limit data and convert to safe format
        else:
            sanitized[key] = str(value).replace('\n', ' ').replace('\r', '')
    return sanitized

# Validation Function
def validate_output(output):
    """Check the LLM output for unexpected content."""
    forbidden_patterns = ["<script>", "exec(", "os.system(", "import ", "```python", "rm -rf", "DROP TABLE"]
    for pattern in forbidden_patterns:
        if pattern in output:
            raise ValueError(f"Invalid content detected in LLM output: {pattern}")
    return output

# Step 3: Generate Narrative with Efficient Prompts
def narrate_with_llm(summary, visualizations):
    sanitized_summary = sanitize_summary(summary)

 # Prepare concise data summaries for the LLM
    prompt = (
        f"Analyze the following dataset summary and generate a nuanced, structured, and dynamic narrative. Combine advanced storytelling techniques with deeper analytical methods, "
        f"comprehensive statistical exploration, and actionable insights. Integrate vision-based systems and dynamic features to ensure a scalable, robust, and adaptive approach.\n\n"

        f"**Dataset Overview:**\n"
        f"- Rows: {sanitized_summary['num_rows']}\n"
        f"- Columns: {sanitized_summary['num_columns']}\n"
        f"- Missing Values: {sanitized_summary['missing_values']}\n"
        f"- Column Types: {list(sanitized_summary['columns'].keys())}\n"
        f"- Key Statistical Insights: {sanitized_summary['desc_stats_summary']}\n"
        f"- Correlation Summary: {sanitized_summary['corr_matrix_summary']}\n\n"

        f"**Analysis and Exploration Instructions:**\n"
        f"1. **Descriptive Statistics and Processing**:\n"
        f"   - Provide a detailed statistical summary (mean, median, standard deviation, percentiles) for numeric columns.\n"
        f"   - Identify and handle missing values with advanced imputation or flagging methods.\n"
        f"   - Summarize column-wise distributions, highlighting skewness and kurtosis for key variables.\n\n"

        f"2. **Deeper Analytical Observations**:\n"
        f"   - Perform clustering or dimensionality reduction techniques (e.g., PCA) to identify latent patterns.\n"
        f"   - Conduct advanced correlation analysis to detect nonlinear relationships (e.g., Spearman, Kendall).\n"
        f"   - Highlight significant trends, anomalies, or outliers, linking them to possible real-world implications.\n\n"

        f"3. **Visualization Instructions (Excluding Date and ID Columns)**:\n"
        f"   - Do not generate visuals for columns identified as dates or IDs.\n"
        f"   - Focus visualizations on significant numeric or categorical fields, such as key performance indicators or highly correlated variables.\n"
        f"   - Use appropriate graphs for the data type (e.g., scatterplots for numeric relationships, bar charts for categorical comparisons).\n\n"

        f"4. **Dynamic and Vision-Based Features**:\n"
        f"   - Apply visual analysis techniques (e.g., image clustering, feature extraction) to detect trends or anomalies if the dataset includes visual elements.\n"
        f"   - Dynamically generate interactive graphs (e.g., heatmaps, scatterplots, pair plots) to enhance the understanding of complex relationships.\n\n"

        f"5. **Integrated Narrative Generation**:\n"
        f"   - Synthesize insights from statistical and deeper analytical methods into a cohesive narrative.\n"
        f"   - Provide actionable recommendations and potential next steps based on the findings.\n"
        f"   - Ensure the narrative dynamically adapts to patterns or anomalies identified during analysis.\n\n"

        f"6. **Scalability and Efficiency Optimization**:\n"
        f"   - Implement optimized techniques for handling large datasets (e.g., batch processing, lazy loading).\n"
        f"   - Reduce memory usage by leveraging reusable logic and efficient library calls.\n"
        f"   - Highlight opportunities for runtime optimization in the provided code.\n\n"

        f"7. **Vision and Agentic Capabilities**:\n"
        f"   - Integrate advanced vision systems for tasks like anomaly detection, object recognition, or trend prediction in visual datasets.\n"
        f"   - Highlight any agentic tasks that can be automated or require decision-making processes linked to the dataset insights.\n\n"

        f"**Formatting and Output Guidelines:**\n"
        f"- Use Markdown formatting with clear subheadings (e.g., 'Descriptive Statistics,' 'Advanced Analysis,' 'Vision-Based Insights').\n"
        f"- Exclude visuals for date or ID columns, focusing on other significant fields.\n"
        f"- Include graphs and tables where applicable, ensuring they directly support the narrative.\n"
        f"- Summarize key findings in bullet points, linking them to actionable recommendations.\n"
        f"- Provide reproducible, modular code snippets for key operations like missing data handling, clustering, and visualization.\n\n"

        f"**Key Enhancements:**\n"
        f"1. Combine deeper analytical methods with descriptive statistics to uncover latent patterns and relationships.\n"
        f"2. Exclude visualizations for date and ID columns, focusing on fields with analytical significance.\n"
        f"3. Optimize runtime performance for large datasets using advanced processing techniques.\n"
        f"4. Dynamically integrate vision-based capabilities and advanced statistical insights into the analysis.\n"
        f"5. Generate a cohesive narrative that is actionable, adaptable, and rich in detail, ensuring seamless integration with code outputs.\n"
    )
    
    data = {
    "model":"gpt-4o-mini",
    "messages":[
                {"role": "system", "content": "You are a concise and insightful data analyst."},
                {"role": "user", "content": prompt}
            ]
    } 

    try:
        response = requests.post(url, headers=headers,json=data)
        return validate_output(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        return f"Error generating narrative: {e}"

# Step 4: Generate README.md
def generate_readme(narrative, visualizations, summary):
    with open("README.md", "w") as readme_file:
        # Add Title
        readme_file.write("# Automated Data Analysis Report\n\n")

        # Data Description
        readme_file.write("## Dataset Description\n\n")
        readme_file.write(f"- **Number of Rows:** {summary['num_rows']}\n")
        readme_file.write(f"- **Number of Columns:** {summary['num_columns']}\n")
        readme_file.write(f"- **Missing Values:** {summary['missing_values']}\n")
        readme_file.write("### Key Descriptive Statistics\n")
        if summary['desc_stats_summary'] is not None:
            readme_file.write(summary['desc_stats_summary'].to_markdown() + "\n\n")

        # Narrative
        readme_file.write("## Narrative Analysis\n\n")
        readme_file.write(narrative + "\n\n")
        
        # Visualizations
        readme_file.write("## Visualizations\n\n")
        for vis_path in visualizations:
            filename = os.path.basename(vis_path)
            readme_file.write(f"![{filename}]({filename})\n\n")


# Main Function
def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    print(f"Processing file: {file_path}...")
    data, summary = analyze_dataset(file_path)
    visualizations = visualize_data(data, summary)
    narrative = narrate_with_llm(summary, visualizations)
    generate_readme(narrative, visualizations, summary)
    print("Analysis is complete. Results are saved in README.md")

# Entry Point
if __name__ == "__main__":
    main()