# import ray
# import modin.pandas as md
import pandas as pd
import numpy as np
import time

#import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

import folium
from folium.plugins import HeatMap, AntPath
from streamlit_folium import folium_static
import streamlit as st
import json
import requests
from PIL import Image
#df = pd.read_parquet('./df_loc_airlinename.parquet')
#_df_loc_airline = pd.DataFrame(df, columns=df.columns)

#AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
#columns = ['AirportID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz_dbTimezone', 'Type', 'Source']
#airports_df = pd.read_csv(AIRPORTS_URL, header=None, names=columns, usecols=['Name', 'IATA', 'Latitude', 'Longitude'])
usa_airports = pd.read_csv('./airports.csv')
# 미국 공항만 필터링s
#usa_airports = airports_df[airports_df['IATA'].str.len() == 3]  # IATA 코드가 3자리인 공항만 선택
usa_airports = usa_airports.dropna(subset=['Latitude', 'Longitude'])  # 위도 경도가 없는 공항은 제외

origin_Df = pd.read_csv('./origin.csv')
stopover_Df = pd.read_csv('./stopover.csv')
destination_Df = pd.read_csv('./destination.csv')
# def plot_price_distribution_by_airline(origin, destination):

#     filtered_df = _df_loc_airline[(_df_loc_airline['Origin'] == origin) & (_df_loc_airline['Destination'] == destination)]
#     pt_airline = pd.pivot_table(filtered_df.fillna(0), index='1st_airline', columns='2st_airline', values='Price', aggfunc=np.mean)
#     pt_airline.rename(columns={0:'Direct'}, inplace=True)

#     # 히트맵 그리기
#     plt.figure(figsize=(10, 7))  # 히트맵 크기 설정
#     sns.heatmap(pt_airline.fillna(0), annot=True, fmt=".0f", cmap="YlGnBu", linewidths=.5)
#     plt.title('Average Flight Price by Airline for {} to {}'.format(origin, destination))
#     plt.ylabel('1st Airline')
#     plt.xlabel('2nd Airline')
#     #plt.show()
#     st.pyplot(plt)


    
    #path.add_to(map_folium)

main_url = "https://6f45-34-29-50-0.ngrok-free.app"  
st.set_page_config(layout="wide")

if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

# 첫 페이지: 출발지, 목적지 등을 입력받아 지도에 표시, 가격 예측
def main_page():
    st.title('US Airports and Flight Price Analysis')
    st.header("Flight Details Input")

    col1, col2, col3 = st.columns(3)
    with col1:
        origin_airport = st.selectbox("Select Origin Airport:", origin_Df.values.reshape(1, -1).tolist()[0],key='origin')

    with col2:
        destination_airport = st.selectbox("Select Destination Airport:", destination_Df.values.reshape(1, -1).tolist()[0], key='destination')

    with col3:
        stop_over_airport = st.selectbox("Select Stop-Over Airport (Optional):", ['None'] + stopover_Df.values.reshape(1, -1).tolist()[0], key='stop_over')

    col4, col5 = st.columns(2)
    with col4:
        start_date = st.date_input("Select Start Date:", key='start_date')

    with col5:
        start_hour = st.selectbox("Select Start Hour:", range(0,24), key='start_hour')

    if st.button("Get Prediction"):
        data = {
            'Origin': origin_airport,
            'Destination': destination_airport,
            'Stopover': stop_over_airport,
            'origin_start_date': start_date.strftime('%Y-%m-%d'),
            'origin_start_date_hour': start_hour
        }
        print(data)
        url = main_url + "/predict"
        response = requests.post(url, json=data)
        if response.status_code == 200:
            prediction = response.json()
            st.write("Prediction Result:", prediction)
            if 'prediction' not in st.session_state:
                st.session_state['prediction'] = prediction
                print(st.session_state['prediction'])
        else:
            st.error("Failed to get prediction from the server.")
        

    #if st.session_state['page'] == 'home' and origin_airport and destination_airport and origin_airport != destination_airport:
    if origin_airport and destination_airport and origin_airport != destination_airport:  
        map_center = [usa_airports['Latitude'].mean(), usa_airports['Longitude'].mean()]
        map_folium = folium.Map(location=map_center, zoom_start=4)
        
        for _, airport in usa_airports.iterrows():
            folium.CircleMarker(
                location=[airport['Latitude'], airport['Longitude']],
                radius=3,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=airport['IATA']).add_to(map_folium)
    
        highlight_airports = [origin_airport, destination_airport]
        highlight_airports_col = ['green', 'red']
        

        if stop_over_airport != 'None':
            highlight_airports.append(stop_over_airport)
            highlight_airports_col.append('orange')

        airport_color_mapping = {airport: color for airport, color in zip(highlight_airports, highlight_airports_col)}


        for _, row in usa_airports[usa_airports['IATA'].isin(highlight_airports)].iterrows():
            color = 'blue'
            popup_text = row['IATA']
            if row['IATA'] in airport_color_mapping:
                color = airport_color_mapping[row['IATA']]
                popup_text += f" ({'Origin' if row['IATA'] == origin_airport else 'Destination' if row['IATA'] == destination_airport else 'Stopover'})"
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=10,
                popup=row['IATA'],
                color=color,
                fill=True,
                fill_color=color,
            ).add_to(map_folium)

            folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    icon=folium.DivIcon(
                    icon_size=(200,36),
                    icon_anchor=(0,0),
                    html=f'<div style="font-size: 12pt; color : {color};">{popup_text}</div>',
            )
            ).add_to(map_folium)
            
        folium_static(map_folium)
        
        #st.markdown(f"### Analysis for {origin_airport} to {destination_airport} from {start_date}")
        
        #image = Image.open('./images/atltobos.png')
        #st.image(image, caption='Average Flight Price by Airline for ATL to BOS', use_column_width=True)

    if st.button("Plan Travel"):
        print(st.session_state['page'] is None)
        st.session_state['page'] = 'travel_plan'
        st.experimental_rerun()
        print(st.session_state['page'])

# 두번째 페이지: 여행 계획 제출
def travel_plan_page():
    st.title("Travel Plan")
    st.write("Welcome to the travel plan page.")

    if 'prediction' in st.session_state:
        st.write("Based on your prediction:", st.session_state['prediction'])
    
    col1, col2= st.columns(2)
    with col1:
        isBasicEconomy = st.selectbox("Basic Economy:", ['None','Yes', 'No'], key='basic_economy_ga')

    with col2:
        isRefundable = st.selectbox("Refundable:", ['None', 'Yes', 'No'], key='Refundable_ga')

    col3, col4, col5 = st.columns(3)
    with col3:
        origin_airport = st.selectbox("Select Origin Airport:", origin_Df.values.reshape(1, -1).tolist()[0], key='origin')

    with col4:
        destination_airport = st.selectbox("Select Destination Airport:", destination_Df.values.reshape(1, -1).tolist()[0], key='destination')

    with col5:
        stop_over_airport = st.selectbox("Select Stop-Over Airport (Optional):", ['None'] + stopover_Df.values.reshape(1, -1).tolist()[0], key='stop_over')
    
    col6, col7 = st.columns(2)
    with col6:
        first_airline = st.selectbox("Select first airline (Optional):", ['None', 'Alaska Airlines', 'American Airlines', 'Boutique Air', 'Cape Air',
                                                                          'Contour Airlines', 'Delta', 'Frontier Airlines', 'Hawaiian Airlines',
                                                                          'JetBlue Airways', 'Key Lime Air', 'Southern Airways Express',
                                                                          'Sun Country Airlines', 'United'], key='first_airline')
    with col7:    
        second_airline = st.selectbox("Select second airline (Optional):", ['None', 'Alaska Airlines', 'American Airlines', 'Boutique Air', 'Cape Air',
                                                                            'Contour Airlines', 'Delta', 'Frontier Airlines', 'JetBlue Airways',
                                                                            'Key Lime Air', 'Silver Airways', 'Southern Airways Express',
                                                                            'Sun Country Airlines', 'United'], key='second_airline')
    col8, col9 = st.columns(2)
    with col8:
        first_cabin = st.selectbox("Select first cabin (Optional):", ['None', 'business', 'coach', 'first', 'premium coach'], key='first_cabin')
    with col9:
        second_cabin = st.selectbox("Select second cabin (Optional):", ['None', 'business', 'coach', 'first', 'premium coach'], key='second_cabin')

    col10, col11 = st.columns(2)
    with col10:
        first_airplane = st.selectbox("Select first airplane (Optional):", ['None', 'AIRBUS INDUSTRIE A321 SHARKLETS', 'AIRBUS INDUSTRIE A350-900',
                                                                            'Airbus A220-100', 'Airbus A319', 'Airbus A319-321', 'Airbus A320',
                                                                            'Airbus A321', 'Airbus A330-200', 'Airbus A330-300', 'BOEING 777-300ER',
                                                                            'BOEING 787-9', 'Boeing 717', 'Boeing 737', 'Boeing 737 MAX 8',
                                                                            'Boeing 737 MAX 9', 'Boeing 737-700', 'Boeing 737-800',
                                                                            'Boeing 737-900', 'Boeing 757', 'Boeing 757-200', 'Boeing 757-300',
                                                                            'Boeing 767', 'Boeing 767-300', 'Boeing 777', 'Boeing 777-200',
                                                                            'Boeing 787', 'Boeing 787-8', 'Canadair Regional Jet',
                                                                            'Canadair Regional Jet 900', 'Canadian Regional Jet 700', 'Cessna',
                                                                            'Embraer 170', 'Embraer 175', 'Embraer 175 (Enhanced Winglets)',
                                                                            'Embraer 190', 'Embraer EMB-145', 'Embraer RJ145',
                                                                            'Fairchild Dornier 328', 'Metro', 'Pilatus PC-12',
                                                                            'Tecnam P2012 Traveler'], key='first_airplane')
    with col11:
        second_airplane = st.selectbox("Select second airplane (Optional):", ['None','AIRBUS INDUSTRIE A321 SHARKLETS', 'AIRBUS INDUSTRIE A350-900',
                                                                            'ATR 42-300/320                                                                                      ',
                                                                            'ATR 72', 'Airbus A220-100', 'Airbus A319', 'Airbus A319-321',
                                                                            'Airbus A320', 'Airbus A321', 'Airbus A330-200', 'Airbus A330-300',
                                                                            'BOEING 777-300ER', 'BOEING 787-9', 'Boeing 717', 'Boeing 737',
                                                                            'Boeing 737 MAX 8', 'Boeing 737 MAX 9', 'Boeing 737-700',
                                                                            'Boeing 737-800', 'Boeing 737-900', 'Boeing 757', 'Boeing 757-200',
                                                                            'Boeing 757-300', 'Boeing 767', 'Boeing 767-300', 'Boeing 777',
                                                                            'Boeing 777-200', 'Boeing 787-8', 'Canadair Regional Jet',
                                                                            'Canadair Regional Jet 900', 'Canadian Regional Jet 700', 'Cessna',
                                                                            'Dehavilland DHC-8 400', 'Embraer 170', 'Embraer 175',
                                                                            'Embraer 175 (Enhanced Winglets)', 'Embraer 190', 'Embraer EMB-145',
                                                                            'Embraer RJ145', 'Fairchild Dornier 328', 'Metro',
                                                                            'NOTE:  THIS IS BUS SERVICE', 'Pilatus PC-12', 'Tecnam P2012 Traveler'], key='second_airplane')
    col12, col13,col14 = st.columns(3)
    with col12:
        start_date = st.date_input("Select Start Date:", key='start_date')

    with col13:
        start_hour = st.selectbox("Select Start Hour:",['None'] + list(range(0,24)), key='start_hour')                                                                                         

    with col14:
        budget = st.text_input('Budget', key='budget')
    

    # destination = st.text_input('Destination', key='destination')
    # budget = st.text_input('Budget', key='budget')

    if st.button("Submit Plan"):
        plan_data = {
                    'isBasicEconomy' : isBasicEconomy,
                    'isRefundable' : isRefundable,
                    'seatsRemaining' : '9',
                    'Origin': origin_airport,
                    'Stopover' : stop_over_airport,
                    'Destination' : destination_airport,
                    'first_airplane' : first_airplane,
                    'second_airplane' : second_airplane,
                    'first_cabin' : first_cabin, #'coach',
                    'second_cabin': second_cabin,
                    'first_airline': first_airline,
                    'second_airline': second_airline,
                    'origin_start_date': start_date.strftime('%Y-%m-%d'),
                    'origin_start_date_hour' : start_hour,
                    'fareBasicCode_f' : 'Q',
                    'budget' : budget}
        print(plan_data)
        
        plan_url = main_url + "/plan"
        response = requests.post(plan_url, json=plan_data)

        if response.status_code == 200:
            result = response.json()
            #st.success("Plan submitted successfully: " + result['budget']) #str(result))
            st.success("Optimal Plan is below") #str(result))
            result_df = pd.DataFrame([result]) # 리스트 내 결과를 DataFrame으로 변환
            result_df['isBasicEconomy'] = np.where(result_df['isBasicEconomy'] == 1, 'Yes', 'No')
            result_df['isRefundable'] = np.where(result_df['isRefundable'] == 1, 'Yes', 'No')
            result_df.drop(['seatsRemaining', 'fareBasicCode_f'], axis=1, inplace=True)

            map_center = [usa_airports['Latitude'].mean(), usa_airports['Longitude'].mean()]
            map_folium = folium.Map(location=map_center, zoom_start=4)
        
            for _, airport in usa_airports.iterrows():
                folium.CircleMarker(
                    location=[airport['Latitude'], airport['Longitude']],
                    radius=3,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6,
                    popup=airport['IATA']).add_to(map_folium)
        
            highlight_airports = [result['Origin'], result['Destination'],result['Stopover']]
            highlight_airports_col = ['green', 'red', 'orange']
            airport_color_mapping = {airport: color for airport, color in zip(highlight_airports, highlight_airports_col)}
            # if stop_over_airport != 'None':
            #     highlight_airports.append(result['Stopover'])

            def draw_path(airport1, airport2, color):
                loc1 = usa_airports[usa_airports['IATA'] == airport1][['Latitude', 'Longitude']].values[0]
                loc2 = usa_airports[usa_airports['IATA'] == airport2][['Latitude', 'Longitude']].values[0]
                path = AntPath(
                    locations=[loc1, loc2],
                    dash_array=[10, 20],
                    delay=1000,
                    color=color,
                    pulse_color='white',
                    ).add_to(map_folium)
  
            for _, row in usa_airports[usa_airports['IATA'].isin(highlight_airports)].iterrows():
                color = 'blue'
                popup_text = row['IATA']
                if row['IATA'] in airport_color_mapping:
                    color = airport_color_mapping[row['IATA']]
                    popup_text += f" ({'Origin' if row['IATA'] == result['Origin'] else 'Destination' if row['IATA'] == result['Destination'] else 'Stopover'})"
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=10,
                    popup=row['IATA'],
                    color=color,
                    fill=True,
                    fill_color=color,
                ).add_to(map_folium)

                # 화살표 경로
                draw_path(result['Origin'], result['Stopover'], 'orange')
                draw_path(result['Stopover'], result['Destination'], 'red')

                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    icon=folium.DivIcon(
                    icon_size=(200,36),
                    icon_anchor=(0,0),
                    html=f'<div style="font-size: 12pt; color : {color};">{popup_text}</div>',
            )
        ).add_to(map_folium)
        
            folium_static(map_folium)
                

            st.table(result_df.melt(var_name="feature", value_name='value'))  # 또는 st.dataframe(result_df) 
        else:
            st.error("Failed to submit plan.")

    if st.button("Back to Home"):
        st.session_state['page'] = 'home'
        st.experimental_rerun()

# 앱 실행
def app():
    if st.session_state['page'] == 'home':
        main_page()
    elif st.session_state['page'] == 'travel_plan':
        travel_plan_page()





if __name__ == "__main__":
    app()

# def app():
#     st.title('US Airports and Flight Price Analysis')
    
#     # 공항 선택
#     origin_airport = st.selectbox("Select Origin Airport:", usa_airports['IATA'], key='origin')
#     destination_airport = st.selectbox("Select Destination Airport:", usa_airports['IATA'], key='destination')
    
#     if origin_airport and destination_airport and origin_airport != destination_airport:
#         # 지도를 위한 레이아웃 분할
#         col1, col2 = st.columns(2) # 두 열로 레이아웃 분할
        
#         with col1:  # 첫 번째 열에 지도 표시
#             map_center = [usa_airports['Latitude'].mean(), usa_airports['Longitude'].mean()]
#             map_folium = folium.Map(location=map_center, zoom_start=4)
            
#             for _, airport in usa_airports.iterrows():
#                 folium.CircleMarker(
#                     location=[airport['Latitude'], airport['Longitude']],
#                     radius=3,
#                     color='blue',
#                     fill=True,
#                     fill_color='blue',
#                     fill_opacity=0.6,
#                     popup=airport['IATA']).add_to(map_folium)

#             for _, row in usa_airports[usa_airports['IATA'].isin([origin_airport, destination_airport])].iterrows():
#                 folium.CircleMarker(
#                     location=[row['Latitude'], row['Longitude']],
#                     radius=10,
#                     popup=row['IATA'],
#                     color='red',
#                     fill=True,
#                     fill_color='red',
#                 ).add_to(map_folium)
            
#             folium_static(map_folium)
        
#         with col2:  # 두 번째 열에 heatmap(분석 결과) 표시
#             st.markdown(f"### Analysis for {origin_airport} to {destination_airport}")
#             plot_price_distribution_by_airline(origin_airport, destination_airport)
#     else:
#         st.error("Please select two different airports to see the analysis.")

# if __name__ == "__main__":
#     app()
