"""
This Python script processes a CSV file containing dissimilarity indexes between future and current cities originally based on bioclimatic variables. 
The script reads the CSV file, calculates the top three most similar current cities for each future city based on their dissimilarity scores, 
and outputs a new CSV file with seven columns detailing these relationships.
matrix source https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6619606/


Columns in the output CSV:
- City in 2050: Name of the future city.
- Today city 1 name: Name of the most similar current city.
- Today city 1 value: Dissimilarity index for the most similar city.
- Today city 2 name: Name of the second most similar current city.
- Today city 2 value: Dissimilarity index for the second most similar city.
- Today city 3 name: Name of the third most similar current city.
- Today city 3 value: Dissimilarity index for the third most similar city.
"""

import pandas as pd

def load_and_process_data(file_path):
    try:
        city_data = pd.read_csv(file_path)
    except FileNotFoundError:
        print("The specified file was not found. Please check the file path.")
        return None

    city_data = city_data.dropna(axis=1, how='all')
    all_rows = []  # List to hold each row before concatenation

    current_cities = city_data.iloc[:, 0]
    future_cities = city_data.columns[1:]

    for future_city in future_cities:
        dissimilarities = city_data[future_city]
        city_dissimilarity_df = pd.DataFrame({
            "Current City": current_cities,
            "Dissimilarity": dissimilarities
        })
        sorted_cities = city_dissimilarity_df.sort_values(by="Dissimilarity").head(3)

        # Collect data only if there are exactly 3 top cities available
        if len(sorted_cities) == 3:
            row = pd.DataFrame({
                "City in 2050": [future_city.replace("Future_", "")],
                "Today city 1 name": [sorted_cities.iloc[0]['Current City']],
                "Today city 1 value": [sorted_cities.iloc[0]['Dissimilarity']],
                "Today city 2 name": [sorted_cities.iloc[1]['Current City']],
                "Today city 2 value": [sorted_cities.iloc[1]['Dissimilarity']],
                "Today city 3 name": [sorted_cities.iloc[2]['Current City']],
                "Today city 3 value": [sorted_cities.iloc[2]['Dissimilarity']]
            })
            all_rows.append(row)

    # Concatenate all rows into a single DataFrame
    if all_rows:
        similar_cities_df = pd.concat(all_rows, ignore_index=True)
    else:
        similar_cities_df = pd.DataFrame()

    return similar_cities_df

def save_results(df, output_path):
    if df is not None and not df.empty:
        df.to_csv(output_path, index=False)
        print("Data processing complete. Results saved to:", output_path)
    else:
        print("No data to save or dataframe was empty.")

# Example usage
file_path = 'city-vs-future-city.csv'  # Update this to the correct path
output_path = 'similar_cities.csv'

results_df = load_and_process_data(file_path)
save_results(results_df, output_path)
