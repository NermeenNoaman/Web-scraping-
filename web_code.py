import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from wordcloud import WordCloud

# ============ Initialize the page ===========
st.set_page_config(layout="wide", page_title="Alexandria Weather Dashboard", page_icon="🌤️")

# ======== Header Section ========
st.title("🌤️ Alexandria Weather Dashboard")
st.markdown("""
    <div style="text-align: right;">
    <h3>Historical Weather Data Analysis</h3>
    <p>Interactive visualization of weather patterns</p>
    </div>
    """, unsafe_allow_html=True)

# ======== Data Loading ========
@st.cache_data
def load_data():
      try:
        # Connect to MongoDB Atlas using secrets from Streamlit
        client = MongoClient(st.secrets["MONGO_URI"])
        db = client[st.secrets["DB_NAME"]]
        collection = db[st.secrets["COLLECTION_NAME"]]

        # Load data from MongoDB
        data = list(collection.find())
        df = pd.DataFrame(data)

        # Clean DataFrame
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

        # Handle date columns
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.month
            df['Month_Name'] = df['Date'].dt.month_name()

        return df

      except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame()

# Load the data
df = load_data()


# ======== Data Visualizations ========
if not df.empty:

    # 1. Weather Distribution Pie Chart
    st.markdown("---")
    st.header("☁️ Weather Conditions Distribution")
    weather_counts = df["Weather"].value_counts().sort_values(ascending=False).head()
    colors = sns.color_palette("pastel").as_hex()
    plt.figure(figsize=(15, 15))

    fig = px.pie(
        names=weather_counts.index,
        values=weather_counts.values,
        title="Proportion of Weather Conditions",
        color_discrete_sequence=colors
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. Correlation Heatmap
    st.markdown("---")
    st.title("🔍 Features Correlation")
    st.header("Heatmap to visualize the correlation between the numerical features")
    features = ["Temperature(°C)", "Humidity (%)", "Barometer (inHg)"]
    if all(feature in df.columns for feature in features):
        corr_matrix = df[features].corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)

    # 3. Weather Frequency Bar Chart
    st.markdown("---")
    st.title("📊 Most Frequent Weather Conditions")
    st.header("Bar Chart to display the frequency of Weather Conditions")
    if "Weather" in df.columns:
        weather_counts = df["Weather"].value_counts().nlargest(10)
        fig = px.bar(weather_counts,
                     orientation='h',
                     color=weather_counts.index,
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     labels={'value': 'Count', 'index': 'Weather Condition'})
        st.plotly_chart(fig, use_container_width=True)

    # 4. Monthly Temperature Extremes
    #Line plot
    st.markdown("---")
    st.title("🌡️ Monthly Temperature Extremes")
    st.header("Line plot for comparing the min & max temperature for each month")
    if 'Month' in df.columns and 'Temperature(°C)' in df.columns:
        monthly_temp = df.groupby('Month')["Temperature(°C)"].agg(['min', 'max']).reset_index()
        monthly_temp_melted = monthly_temp.melt(id_vars='Month', value_vars=['min', 'max'],
                                                var_name='Metric', value_name='Temperature')

        fig = px.line(
            monthly_temp_melted,
            x='Month',
            y='Temperature',
            color='Metric',
            markers=True,
            color_discrete_sequence=['skyblue', 'salmon'],
            labels={'Temperature': 'Temperature (°C)', 'Month': 'Month'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # 5. Temperature Distribution Histogram
    st.markdown("---")
    st.header("📈 Temperature Distribution")
    if 'Temperature(°C)' in df.columns:
        fig_hist = px.histogram(df, x='Temperature(°C)', nbins=20,
                                title='Histogram',
                                color_discrete_sequence=['skyblue'])
        st.plotly_chart(fig_hist, use_container_width=True)

    # 6.Comparing the temperature distribution for each month using boxplots
    fig = px.box(df, x='Month', y='Temperature(°C)',
                 title='Monthly Temperature Variability',
                 labels={'Month': 'Month', 'Temperature': 'Temperature (°C)'},
                 points='outliers',
                 template='plotly_white',
                 color_discrete_sequence=['#40E0D0'])
    fig.update_layout()
    st.plotly_chart(fig, use_container_width=True)

    # 7. Scatter Plot: Temperature vs Humidity
    st.markdown("---")
    st.header("💧 Temperature vs Humidity")
    if 'Temperature(°C)' in df.columns and 'Humidity (%)' in df.columns:
        fig_scatter1 = px.scatter(
            df,
            x='Humidity (%)',
            y='Temperature(°C)',
            title='Relationship between Temperature and Humidity',
            trendline='ols'
        )
        st.plotly_chart(fig_scatter1, use_container_width=True)

    # 8. Scatter Plot: Temperature vs Barometer
    if 'Temperature(°C)' in df.columns and 'Barometer (inHg)' in df.columns:
        fig_scatter2 = px.scatter(
            df,
            x='Barometer (inHg)',
            y='Temperature(°C)',
            title='Relationship between Temperature and Barometer',
            trendline='ols'
        )
        st.plotly_chart(fig_scatter2, use_container_width=True)

        # 9.  Stacked barchart to get top 10 most frequent wind types in data with respect to each month

        st.header("Stacked Barchart to get top 10 most frequent wind types in data with respect to each month")
        # Get top 10 most frequent wind types across the whole dataset
        top_10_wind_types = df['Wind (mph)'].value_counts().nlargest(10).index

        # Filter the DataFrame to only include top 10 wind types
        df_top_wind = df[df['Wind (mph)'].isin(top_10_wind_types)]

        # Count wind values by month (pivot table for stacked bar)
        wind_counts = df_top_wind.pivot_table(index='Month', columns='Wind (mph)', aggfunc='size', fill_value=0)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        wind_counts.plot(kind='bar', ax=ax, colormap='RdBu', stacked=True)

        # Customize plot
        ax.set_title('Monthly Wind Conditions (Stacked)')
        ax.set_xlabel('Month')
        ax.set_ylabel('Frequency')
        ax.tick_params(axis='x', rotation=0)
        plt.tight_layout()
        ax.legend(title='Wind Type', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Display in Streamlit
        st.pyplot(fig)

    # 10. Word Cloud for Weather Conditions
    st.markdown("---")
    st.header("☁️ Weather Word Cloud")
    if 'Weather' in df.columns:
        weather_text = ' '.join(df['Weather'].astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(weather_text)
        fig_wc, ax_wc = plt.subplots(figsize=(12, 6))
        ax_wc.imshow(wordcloud, interpolation='bilinear')
        ax_wc.axis('off')
        st.pyplot(fig_wc)

else:
    st.warning("⚠️ No data available for visualization.")
