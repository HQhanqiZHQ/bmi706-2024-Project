import pandas as pd
import requests
from io import StringIO
import altair as alt
import streamlit as st

import base64
import os

alt.data_transformers.disable_max_rows()

# creates custom sorting of age groups
# Credit to https://github.com/vega/altair/issues/1826
# for helping with this line.
sorted_age_groups = ["<1 year", "1 to 4", "5 to 9", "10 to 14", "15 to 19", "20 to 24", "25 to 29", "30 to 34", "35 to 39", "40 to 44", "45 to 49", "50 to 54", "55 to 59", "60 to 64", "65 to 69", "70 to 74", "75 to 79", "80 to 84", "85 plus"]

@st.cache
def load_data_from_github(repo_owner, repo_name, file_path, branch='main'):
    """Load CSV data from a GitHub repository."""
    try:
        url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        
        return df
    except Exception as e:
        print(f"An error occurred while loading the file: {str(e)}")
        return None

# Creates the chart for Section 1
def age_group_chart(data):
    """Create a line chart of mortality rates by age group and demographic."""

    # Filters data to just ordinal age categories
    data_subset = data[data["age_name"].isin(sorted_age_groups)]

    # Credit to https://altair-viz.github.io/gallery/line_chart_with_points.html
    # for help with adding points
    return alt.Chart(data_subset).mark_line(point=True).encode(
        x=alt.X('age_name:O', sort=sorted_age_groups, title='Age Group'),
        y=alt.Y('val:Q', title='Mortality Rate'),
        color=alt.Color('race_name:N', sort=["Total", "AIAN", "Asian", "Black", "Latino", "White"], title='Racial Group'),
        tooltip=['age_name', 'race_name', 'val']
    ).properties(
        width=600,
        height=400,
        title='Mortality Rates by Age Group and Demographic Group'
    ).interactive()


# Creates the age-based chart for section 2
def time_series_chart_age(data, selector):
    """Create a line chart of mortality rates over time grouped by age."""
    #selector = alt.selection_single(fields=['age_name'], bind='legend')
    
    # Filters data to appropriate age, race, and sex values
    data_subset = data[data["age_name"].isin(sorted_age_groups)]
    data_subset = data_subset[data_subset["race_name"] == "Total"]
    data_subset = data_subset[data_subset["sex_name"] == "Both"]

    # Credit to https://altair-viz.github.io/gallery/line_chart_with_points.html
    # for help with adding points
    return alt.Chart(data_subset).mark_line(point=True).encode(
        x=alt.X('year:T', title='Year'),
        y=alt.Y('val:Q', title='Mortality Rate'),

        # Credit to https://vega.github.io/vega/docs/schemes/
        # and https://altair-viz.github.io/user_guide/customization.html
        # for help with color schemes
        color=alt.Color('age_name:N', sort=sorted_age_groups, title="Age Group").scale(scheme="yelloworangered"),
        tooltip=['year', 'age_name', 'val']
    ).add_selection(
        selector
    ).transform_filter(
        selector
    ).properties(
        width=600,
        height=500,
        title='Mortality Rates Over Time Categorized by Age Group'
    )


# Creates the sex-based chart for section 2
def time_series_chart_sex(data, selector):
    """Create a line chart of mortality rates over time grouped by sex."""
    #selector = alt.selection_single(fields=['sex_name'], bind='legend')
    
    # Filters data to appropriate age, race, and sex values
    data_subset = data[data["age_name"] == "All Ages"]
    data_subset = data_subset[data_subset["race_name"] == "Total"]

    # Credit to https://altair-viz.github.io/gallery/line_chart_with_points.html
    # for help with adding points
    return alt.Chart(data_subset).mark_line(point=True).encode(
        x=alt.X('year:T', title='Year'),
        y=alt.Y('val:Q', title='Mortality Rate'),

        # Credit to https://vega.github.io/vega/docs/schemes/
        # and https://altair-viz.github.io/user_guide/customization.html
        # for help with color schemes
        color=alt.Color('sex_name:N', sort=["Both", "Female", "Male"], title="Sex Group"),
        tooltip=['year', 'sex_name', 'val']
    ).add_selection(
        selector
    ).transform_filter(
        selector
    ).properties(
        width=600,
        height=500,
        title='Mortality Rates Over Time Categorized by Sex Group'
    )

# Creates the race-based chart for section 2
def time_series_chart_race(data, selector):
    """Create a line chart of mortality rates over time grouped by race."""
    #selector = alt.selection_single(fields=['race_name'], bind='legend')
    
    # Filters data to appropriate age, race, and sex values
    data_subset = data[data["age_name"] == "All Ages"]
    data_subset = data_subset[data_subset["sex_name"] == "Both"]

    # Credit to https://altair-viz.github.io/gallery/line_chart_with_points.html
    # for help with adding points
    return alt.Chart(data_subset).mark_line(point=True).encode(
        x=alt.X('year:T', title='Year'),
        y=alt.Y('val:Q', title='Mortality Rate'),

        # Credit to https://vega.github.io/vega/docs/schemes/
        # and https://altair-viz.github.io/user_guide/customization.html
        # for help with color schemes
        color=alt.Color('race_name:N', sort=["Total", "AIAN", "Asian", "Black", "Latino", "White"], title="Demographic Group"),
        tooltip=['year', 'race_name', 'val']
    ).add_selection(
        selector
    ).transform_filter(
        selector
    ).properties(
        width=600,
        height=500,
        title='Mortality Rates Over Time Categorized by Demographic Group'
    )

# Creates the overall distribution chart for section 3
def distribution_boxplot(data):

    # Removes total values and non-applicable values from distribution
    data_subset = data[data["race_name"] != "Total"]
    data_subset = data_subset[data_subset["age_name"] != "Age-standardized"]
    data_subset = data_subset[data_subset["age_name"] != "All Ages"]
    data_subset = data_subset[data_subset["sex_name"] != "Both"]

    # 0 values would break the log scaling
    data_subset = data_subset[data_subset["val"] != 0]

    # Credit to https://altair-viz.github.io/user_guide/marks/boxplot.html
    # for helping with mark_boxplot
    return alt.Chart(data_subset).mark_boxplot().encode(
        # Credit to https://stackoverflow.com/questions/58032074/why-is-altair-returning-an-empty-chart-when-using-log-scale
        # and https://stackoverflow.com/questions/62281179/how-to-adjust-scale-ranges-in-altair
        # for help with log scaling
        x = alt.X('val:Q', title="Log-Transformed Mortality Rates With Zero-Values Omitted").scale(type="log", domain=[1E-7, 0.01])
        
    ).properties(
        width=600,
        height=200,
        title='Distribution of Cirrhosis Mortality Data from All Combinations of Subpopulation Groups'

    # Credit to https://altair-viz.github.io/user_guide/customization.html
    # for help with setting the color of the plot
    ).configure_mark(
        color='grey'
    )



# Creates the selected distribution chart for section 3
def selected_distribution_boxplot(data):

    # Removes total values and non-applicable values from distribution
    data_subset = data[data["race_name"] != "Total"]
    data_subset = data_subset[data_subset["age_name"] != "Age-standardized"]
    data_subset = data_subset[data_subset["age_name"] != "All Ages"]
    data_subset = data_subset[data_subset["sex_name"] != "Both"]

    # 0 values would break the log scaling
    data_subset = data_subset[data_subset["val"] != 0]

    # Credit to https://altair-viz.github.io/user_guide/marks/boxplot.html
    # for helping with mark_boxplot
    return alt.Chart(data_subset).mark_boxplot().encode(
        # Credit to https://stackoverflow.com/questions/58032074/why-is-altair-returning-an-empty-chart-when-using-log-scale
        # and https://stackoverflow.com/questions/62281179/how-to-adjust-scale-ranges-in-altair
        # for help with log scaling
        x = alt.X('val:Q', title="Log-Transformed Mortality Rates With Zero-Values Omitted").scale(type="log", domain=[1E-7, 0.01])
        
    ).properties(
        width=600,
        height=200,
        title='Distribution of Cirrhosis Mortality Data from the Selected Combinations of Subpopulation Groups'

    # Credit to https://altair-viz.github.io/user_guide/customization.html
    # for help with setting the color of the plot
    ).configure_mark(
        color='red'
    )


# Displays the charts and other components of the Streamlit app
def display_charts(data):
    """Display all charts based on available data."""
    # create_navigation_buttons()
    # Time period filter
    start_year, end_year = st.slider(
        "Select Time Period",
        min_value=data['year'].min().year,
        max_value=data['year'].max().year,
        value=(data['year'].min().year, data['year'].max().year)
    )
    filtered_data = data[(data['year'].dt.year >= start_year) & (data['year'].dt.year <= end_year)]

    # SECTION 1

    # Credit to https://medium.com/@mosqito85/how-to-use-headings-in-streamlit-st-title-st-header-st-subheader-ede54527a67c
    # for help with formating headers
    st.header("Section 1: Distribution of Cirrhosis Across the Lifespan", anchor="section1")
    st.write("This section shows the distribution of cirrhosis mortality rates across the lifespan.")
    st.write("Use the interactive features to display data corresponding to different years, demographics, and sexes.")
    # Creates interactive widgets for section 1:
    # Credit to problem set 3 for helping with the following lines
    year_select = st.slider("Select Year", min_value=start_year, max_value=end_year)
    age_chart_subset = filtered_data[filtered_data["year"].dt.year == year_select]
    # Credit to problem set 3 for helping with the following lines
    race_group_select = st.multiselect("Select Demographic Groups", options=filtered_data['race_name'].unique(), default=filtered_data['race_name'].unique())
    age_chart_subset = age_chart_subset[age_chart_subset["race_name"].isin(race_group_select)]
    # Credit to problem set 3 for helping with the following lines  
    sex_group_select = st.radio("Select Sex Group", options=["Both", "Male", "Female"])
    age_chart_subset = age_chart_subset[age_chart_subset["sex_name"] == sex_group_select]

    chart = age_group_chart(age_chart_subset)
    chart = chart.properties(width=600, height=400)
    # Plots the chart for section 1:
    st.altair_chart(chart.interactive(), use_container_width=True)




    # SECTION 2

    st.header("Section 2: Distribution of Cirrhosis Over Time in Different Subpopulations", anchor="section2")
    st.write("This section shows how cirrhosis has impacted different subpopulations over the years.")
    st.write("For a more detailed view of a specific subpopulation, click on the subpopulation in its legend.")


    # Creates selectors to be used in section 2
    selector_age = alt.selection_single(fields=['age_name'], bind='legend')
    selector_sex = alt.selection_single(fields=['sex_name'], bind='legend')
    selector_race = alt.selection_single(fields=['race_name'], bind='legend')

    # Creates the three charts in section 2
    st.altair_chart(time_series_chart_age(filtered_data, selector_age).interactive(), use_container_width=True)
    st.altair_chart(time_series_chart_sex(filtered_data, selector_sex).interactive(), use_container_width=True)
    st.altair_chart(time_series_chart_race(filtered_data, selector_race).interactive(), use_container_width=True)



    # SECTION 3

    st.header("Section 3: Visualizing the Disproportionate Impact of Cirrhosis", anchor="section3")
    st.write("This section compares the overall mortality rates of cirrhosis to the rates of the selected subpopulations.")
    st.write("Use the interactive tools to select age, sex, and demographic groups.")
    st.write("The distribution of rates within the selected groups will appear in the red boxplot.")
    st.write("For comparison, the overall distribution of rates will appear in the gray boxplot.")
    st.write("Each point in the boxplot represents one year's mortality data from a specific age, sex, and race.")
    st.write("Hover over the boxplots to view descriptive statistics about the distributions.")

    # Creates interactive selections for section 3

    age_group_multiselect = st.multiselect("Select Specific Age Groups", options=sorted_age_groups, default=sorted_age_groups)
    sex_group_multiselect = st.multiselect("Select Specific Sex Groups", options=["Female", "Male"], default=["Female", "Male"])
    race_group_multiselect = st.multiselect("Select Specific Demographic Groups", options=["AIAN", "Asian", "Black", "Latino", "White"], default=["AIAN", "Asian", "Black", "Latino", "White"])

    # Subsets the data to what is selected

    select_dist_subset = filtered_data[filtered_data["age_name"].isin(age_group_multiselect)]
    select_dist_subset = select_dist_subset[select_dist_subset["sex_name"].isin(sex_group_multiselect)]
    select_dist_subset = select_dist_subset[select_dist_subset["race_name"].isin(race_group_multiselect)]

    # Creates the boxplot with the selected distribution
    st.altair_chart(selected_distribution_boxplot(select_dist_subset).interactive(), use_container_width=True)
    # Creates the boxplot of the overall distribution
    st.altair_chart(distribution_boxplot(filtered_data).interactive(), use_container_width=True)

def load_css(file_name):
    with open(file_name, 'r') as f:
        style = f'<style>{f.read()}</style>'
    return style  

def create_menu_bar():
    menu_html = """
    <div class="menu-bar">
        <a href="#section1">Section 1</a>
        <a href="#section2">Section 2</a>
        <a href="#section3">Section 3</a>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)

def create_navigation_buttons():
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Go to Section 1", key="nav1"):
            st.experimental_set_query_params(section="section1")
    with col2:
        if st.button("Go to Section 2", key="nav2"):
            st.experimental_set_query_params(section="section2")
    with col3:
        if st.button("Go to Section 3", key="nav3"):
            st.experimental_set_query_params(section="section3")

if __name__ == "__main__":
    # st.set_page_config(layout="wide")
    st.markdown(load_css('custom.css'), unsafe_allow_html=True)
    create_menu_bar()
    st.title("Cirrhosis Mortality Analysis")
    repo_owner = "HQhanqiZHQ"
    repo_name = "bmi706-2024-Project"
    file_path = "Combined_USA_Data.csv"

    df = load_data_from_github(repo_owner, repo_name, file_path)

    if df is None:
        print("Data loading failed. Please check the GitHub repository details and file path.")
    else:

        # Convert 'year' to datetime
        df['year'] = pd.to_datetime(df['year'], format='%Y')

        # Filter data for cirrhosis-related causes
        df_cirrhosis = df[df['cause_name'].str.contains('Cirrhosis', case=False)]

        display_charts(df_cirrhosis)
