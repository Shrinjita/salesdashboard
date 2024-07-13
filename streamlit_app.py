import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import plotly.figure_factory as ff
import plotly.graph_objs as go
import plotly.express as px
import scipy
st.set_page_config(layout='wide', initial_sidebar_state='expanded')
with open('style.css') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
def load_data(file_path, parameter1, parameter2):
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()
    data = data[:-1]
    columns_to_select = [parameter1, parameter2, 'Qty(S1)', 'Qty(S2)', '%Qty1', 'Amount(S1)', 'Amount(s2)', 'Amount(1)%']
    data = data[columns_to_select]
    for col in ['Qty(S1)', 'Qty(S2)', '%Qty1', 'Amount(S1)', 'Amount(s2)', 'Amount(1)%']:
        data[col] = data[col].apply(convert_to_int_or_float)
    data = data.dropna(how='all').replace('nan', pd.NA).dropna()
    data['Abs diff in qty'] = data['Qty(S1)'] - data['Qty(S2)']
    data['Abs diff in amt'] = data['Amount(S1)'] - data['Amount(s2)']
    total_Amount_S1 = data['Amount(S1)'].sum()
    total_Amount_S2 = data['Amount(s2)'].sum()
    total_Qty_S1 = data['Qty(S1)'].sum()
    total_Qty_S2 = data['Qty(S2)'].sum()
    data['Revenue1_%total'] = (data['Amount(S1)'] / total_Amount_S1) * 100     
    data['Revenue2_%total'] = (data['Amount(s2)'] / total_Amount_S2) * 100 
    data['Volume1_%total'] = (data['Qty(S1)'] / total_Qty_S1) * 100 
    data['Volume2_%total'] = (data['Qty(S2)'] / total_Qty_S2) * 100
    column_to_select = [
        parameter1, parameter2, 
        'Qty(S1)', 'Volume1_%total', 'Qty(S2)', 'Volume2_%total', 'Abs diff in qty', '%Qty1', 
        'Amount(S1)', 'Revenue1_%total', 'Amount(s2)', 'Revenue2_%total', 'Abs diff in amt', 'Amount(1)%'
    ]
    data = data[column_to_select]
    if file_path == 'statebrand.csv' or file_path == 'branditem.csv':
        totals_row = pd.Series({
            parameter1: 'Total',
            parameter2: '',
            'Qty(S1)': total_Qty_S1,
            'Volume1_%total': '',
            'Qty(S2)': total_Qty_S2,
            'Volume2_%total': '',
            'Abs diff in qty': '',
            '%Qty1': '',
            'Amount(S1)': total_Amount_S1,
            'Revenue1_%total': '',
            'Amount(s2)': total_Amount_S2,
            'Revenue2_%total': '',
            'Abs diff in amt': '',
            'Amount(1)%': ''
        })
        data = pd.concat([data, pd.DataFrame([totals_row])], ignore_index=True)           
        unique_array = data[parameter2].unique() 
        return data, unique_array   
    return data

def convert_to_int_or_float(value):
    if isinstance(value, (int, float)):
        return value
    value = value.replace(',', '')
    try:
        return int(value)
    except ValueError:
        return float(value) 
def format_large_number(number):
    if number >= 10**7:  # Crores
        return f"{number / 10**7:.2f} cr"
    elif number >= 10**5:  # Lacs
        return f"{number / 10**5:.2f} lac"
    else:
        return f"{number:.2f}"
def display_totals_and_means(data):
    columns_to_check = ['Qty(S1)', 'Amount(S1)', 'Qty(S2)', 'Amount(s2)', '%Qty1', 'Amount(1)%']
    for column in columns_to_check:
        if column not in data.columns:
            st.error(f"Missing column: {column}")
            return
    qty_23_24_sum = data['Qty(S1)'].sum()
    amt_23_24_sum = data['Amount(S1)'].sum()
    qty_24_25_sum = data['Qty(S2)'].sum()
    amt_24_25_sum = data['Amount(s2)'].sum()
    qty_diff = qty_24_25_sum - qty_23_24_sum
    amt_diff = amt_24_25_sum - amt_23_24_sum
    qty1_mean = data['%Qty1'].mean()
    amount1_mean = data['Amount(1)%'].mean()
    qty_diff_str = format_large_number(qty_diff)
    amt_diff_str = format_large_number(amt_diff)
    qty1_mean_str = f"{qty1_mean:.2f}%"
    amount1_mean_str = f"{amount1_mean:.2f}%"
    qty_23_24_sum_str = format_large_number(qty_23_24_sum)
    amt_23_24_sum_str = format_large_number(amt_23_24_sum)
    qty_24_25_sum_str = format_large_number(qty_24_25_sum)
    amt_24_25_sum_str = format_large_number(amt_24_25_sum)
    left, center1, center2, right = st.columns([1,4,4,1])
    with left:
        st.write("")
    with right:
        st.write("")
    with center1:
        st.markdown("<div style='text-align: center; justify-content: center; align-items: center;'><style> .dataframe { margin-left: auto; margin-right: auto; } </style>", unsafe_allow_html=True)
        st.metric("Quantity", qty_diff_str, qty1_mean_str)
        st.metric("Q1", qty_23_24_sum_str)
        st.metric("Q2", qty_24_25_sum_str)
        st.markdown("</div>", unsafe_allow_html=True)
    with center2:
        st.markdown("<div style='text-align: center; justify-content: center; align-items: center;'><style> .dataframe { margin-left: auto; margin-right: auto; } </style>", unsafe_allow_html=True)
        st.metric("Amount", amt_diff_str, amount1_mean_str)
        st.metric("A1", amt_23_24_sum_str)
        st.metric("A2", amt_24_25_sum_str)
        st.markdown("</div>", unsafe_allow_html=True)    
    return qty_diff_str, amt_diff_str, qty1_mean_str, amount1_mean_str, qty_23_24_sum_str, amt_23_24_sum_str, qty_24_25_sum_str, amt_24_25_sum_str
def generate_html_table(data_sorted, parameter1, parameter2):
    def create_html_table(data_sorted, parameter1, parameter2):
        table_html = '<div class="data-table-wrapper">'
        table_html += '<table class="data-table">'
        headers = [parameter1, parameter2, 
        'Qty(S1)', 'Volume1_%total', 'Qty(S2)', 'Volume2_%total', 'Abs diff in qty', '%Qty1', 
        'Amount(S1)', 'Revenue1_%total', 'Amount(s2)', 'Revenue2_%total', 'Abs diff in amt', 'Amount(1)%']
        table_html += '<tr>'
        for header in headers:
            table_html += f'<th>{header}</th>'
        table_html += '</tr>'
        for index, row in data_sorted.iterrows():
            table_html += '<tr>'
            for header in headers:
                if header in data_sorted.columns:
                    value = row[header]
                    if pd.notna(value):
                        try:
                            numeric_value = float(value)
                            color = 'red' if numeric_value < 0 else 'green'
                            if '%' in header or 'diff' in header.lower():
                                formatted_value = f"{numeric_value:,.2f}"
                                table_html += f'<td style="color: {color};">{formatted_value}</td>'
                            else:
                                formatted_value = f"{numeric_value:,.2f}"
                                table_html += f'<td>{formatted_value}</td>'
                        except ValueError:
                            table_html += f'<td>{value}</td>'
                    else:
                        table_html += f'<td>{value}</td>'
                else:
                    table_html += '<td></td>'
            table_html += '</tr>'
        table_html += '</table>'
        table_html += '</div>'
        return table_html
    html_table = create_html_table(data_sorted, parameter1, parameter2)
    return html_table

def plot_multi_bar_chart(data, comparison_type, parameter):
    if comparison_type == "Fluctuation in Volume":
        x_values = data[parameter]
        y_values_1 = data['Qty(S1)']
        y_values_2 = data['Qty(S2)']
        y_axis_label_1 = 'Qty(S1)'
        y_axis_label_2 = 'Qty(S2)'
    elif comparison_type == "Volatility in Revenue":
        x_values = data[parameter]
        y_values_1 = data['Amount(S1)']
        y_values_2 = data['Amount(S2)']
        y_axis_label_1 = 'Amount(S1)'
        y_axis_label_2 = 'Amount(S2)'
    elif comparison_type == "Pareto Analysis":
        x_values = data[parameter]
        y_values_1 = data['%Qty1']
        y_values_2 = data['Amount(1)%']
        y_axis_label_1 = 'Fluctuation'
        y_axis_label_2 = 'Volatility'
    elif comparison_type == "Variance Analysis":
        x_values = data[parameter]
        y_values_1 = data['Abs diff in qty']
        y_values_2 = data['Abs diff in amt']
        y_axis_label_1 = 'Quantity'
        y_axis_label_2 = 'Amount'
        
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_values,
        y=y_values_1,
        name=y_axis_label_1,
        marker_color='skyblue'
    ))
    fig.add_trace(go.Bar(
        x=x_values,
        y=y_values_2,
        name=y_axis_label_2,
        marker_color='#437DF1'
    ))
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        xaxis_title=parameter,
        yaxis_title='Values',
        barmode='group',
        title=f'{comparison_type} for {parameter}',
        legend_title='Type',
        margin=dict(l=20, r=20, t=30, b=20),
        height=400
    )
    try:
        st.plotly_chart(fig, use_container_width=True)  # Ensure the chart uses the container width
    except ValueError as e:
        st.error(f"Error plotting chart: {e}")
        
def plot_donut_chart(data, parameter1, donut_option):
    st.markdown('<div class="donut-chart">', unsafe_allow_html=True)
    donut_option_mapping = {
        'Market Share last year in Q1': 'Qty(S1)',
        'Market Share this year in Q1': 'Qty(S2)',
        'Revenue Contribution last year': 'Amount(S1)',
        'Revenue Contribution this year': 'Amount(s2)',
        'Growth in Quantity': '%Qty1',
        'Growth in Revenue': 'Amount(1)%'}
    if donut_option not in donut_option_mapping:
        raise ValueError(f"Invalid donut_option '{donut_option}'")
    column_to_plot = donut_option_mapping[donut_option]
    values = data[column_to_plot].abs()
    filtered_data = select_percentages(values)
    fig = go.Figure(data=[go.Pie(labels=data[parameter1], values=values, hole=.3)])
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        autosize=False,
        width=1600,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),  # Adjusted margins to reduce gap
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.3,
            font=dict(size=16)  # Change the size as needed
        )
    )
    st.plotly_chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)
def select_percentages(percentages):
    sorted_percentages = sorted(percentages, reverse=True)
    current_sum = 0
    selected_percentages = []
    for percentage in sorted_percentages:
        if current_sum + percentage < 50:
            selected_percentages.append(percentage)
            current_sum += percentage
        else:
            break
    return selected_percentages

def narrative(data, parameter):
    def list_to_string(lst):
        return ', '.join(lst)
    
    negative_quantity = list_to_string(data[data['%Qty1'] < 0][parameter].tolist())
    positive_quantity = list_to_string(data[data['%Qty1'] > 0][parameter].tolist())
    neutral_quantity = list_to_string(data[data['%Qty1'] == 0][parameter].tolist())
    
    negative_revenue = list_to_string(data[data['Amount(1)%'] < 0][parameter].tolist())
    positive_revenue = list_to_string(data[data['Amount(1)%'] > 0][parameter].tolist())
    neutral_revenue = list_to_string(data[data['Amount(1)%'] == 0][parameter].tolist())

    narrative = f"""
    <div style="font-size: 18px; font-family: Calibri;">
        <strong>Growth Analysis:</strong><br>
        - <strong style="color:#E5260F;">Negative Performance in Quantity:</strong> {negative_quantity}<br>
        - <strong style="color:#20E50F;">Positive Performance in Quantity:</strong> {positive_quantity}<br>
        - <strong style="color:#FF8000;">Neutral Performance in Quantity:</strong> {neutral_quantity}<br><br>
        - <strong style="color:#E5260F;">Negative Performance in Revenue:</strong> {negative_revenue}<br>
        - <strong style="color:#20E50F;">Positive Performance in Revenue:</strong> {positive_revenue}<br>
        - <strong style="color:#FF8000;">Neutral Performance in Revenue:</strong> {neutral_revenue}<br>
    </div>
    """
    st.markdown(narrative, unsafe_allow_html=True)

def print_blank_lines(n):
    for _ in range(n):
        st.write("")

def plot_histogram(data, y_axis_label, x_axis_label):
    x_values = data[x_axis_label]
    y_values = data[y_axis_label]
    colors = ['red' if y < 0 else 'green' if y > 0 else 'blue' for y in y_values]
    bars = go.Bar(x=x_values, y=y_values, marker=dict(color=colors))
    fig = go.Figure(data=bars)
    fig.update_layout(
        autosize=False,
        width=1600,
        height=650,
        margin=dict(l=10, r=10, t=0, b=10),
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.3,
            font=dict(size=22)  # Change the size as needed
        ),
        yaxis=dict(
            title=y_axis_label,
            title_font=dict(size=22),  # Change the size as needed
            tickfont=dict(size=22)  # Change the size as needed
        ),
        xaxis=dict(
            title=x_axis_label,
            title_font=dict(size=22),  # Change the size as needed
            tickfont=dict(size=22)  # Change the size as needed
        )
    )
    st.plotly_chart(fig)

    top7 = data.nlargest(7, y_axis_label)[[x_axis_label,y_axis_label]]
    bot7 = data.nsmallest(7, y_axis_label)[[x_axis_label,y_axis_label]]
    return top7, bot7

def plot_line_chart(data, line_chart_option, parameter, plot_height1):
    if line_chart_option == 'Qty1 vs Qty2':
        y_values_1 = data['Qty(S1)']
        y_values_2 = data['Qty(S2)']
        y_axis_label_1 = 'Qty(S1)'
        y_axis_label_2 = 'Qty(S2)'
    elif line_chart_option == 'Amt1 vs Amt2':
        y_values_1 = data['Amount(S1)']
        y_values_2 = data['Amount(s2)']
        y_axis_label_1 = 'Amount(S1)'
        y_axis_label_2 = 'Amount(s2)'
    elif line_chart_option == 'Qty1% vs Qty2%':
        y_values_1 = data['Volume1_%total']
        y_values_2 = data['Volume2_%total']
        y_axis_label_1 = 'Volume1_%total'
        y_axis_label_2 = 'Volume2_%total'
    elif line_chart_option == 'Amt1% vs Amt2%':
        y_values_1 = data['Revenue1_%total']
        y_values_2 = data['Revenue2_%total']
        y_axis_label_1 = 'Revenue1_%total'
        y_axis_label_2 = 'Revenue2_%total'
    elif line_chart_option == 'QtyAbsDiff vs AmtAbsDiff':
        y_values_1 = data['Abs diff in qty']
        y_values_2 = data['Abs diff in amt']
        y_axis_label_1 = 'Abs diff in qty'
        y_axis_label_2 = 'Abs diff in amt'
    elif line_chart_option == 'F vs V':
        y_values_1 = data['%Qty1']
        y_values_2 = data['Amount(1)%']
        y_axis_label_1 = 'Fluctuation %'
        y_axis_label_2 = 'Volatility %'
    else:
        st.error("Invalid line chart option selected.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data[parameter], y=y_values_1, mode='lines+markers', name=y_axis_label_1, line=dict(color='rgb(120,30,255)')))
    fig.add_trace(go.Scatter(x=data[parameter], y=y_values_2, mode='lines+markers', name=y_axis_label_2, line=dict(color='rgb(255,132,24)')))
    fig.update_layout(
        autosize=False,
        width=1600,
        height=plot_height1,
        margin=dict(l=20, r=0, t=0, b=40),
        legend=dict(font=dict(size=18)),
        yaxis=dict(
            title='Values',
            title_font=dict(size=18),
            tickfont=dict(size=18)
        ),
        xaxis=dict(
            title=parameter,
            title_font=dict(size=18),
            tickfont=dict(size=18)
        )
    )
    st.plotly_chart(fig)

def main():
    logo = Image.open('LOGO.png')
    st.sidebar.image(logo)
    st.sidebar.markdown('<center><a href="#titles" style="text-decoration: none; font-size: 26px; font-weight:bold;">Dashboard</a></center>', unsafe_allow_html=True)
    st.markdown('<div id="titles"></div>',unsafe_allow_html=True)
    titles = {
        "State": "STATEWISE ANALYSIS",
        "Brand": "BRANDWISE ANALYSIS",
        "Brand Item": "BRAND-ITEM WISE ANALYSIS",
        "State Brandwise": "STATEWISE BRAND ANALYSIS",
        "Sub-Brand": "SUB-BRAND WISE ANALYSIS"
    }
    file_paths = {
        "State": 'state.csv',
        "Brand": 'brand.csv',
        "Brand Item": 'branditem.csv',
        "State Brandwise": 'statebrand.csv',
        "Sub-Brand": 'sub-brand.csv'
    }
    parameters1 = {
        "State": 'STATE',
        "Brand": 'DESC.',
        "Brand Item": 'ITEM',
        "State Brandwise": 'DESC.',
        "Sub-Brand": 'DESC.'
    }
    parameters2 = {
        "State": 'Valuation Type',
        "Brand": 'COST CNTR.',
        "Brand Item": 'DESC.1',
        "State Brandwise": 'STATE',
        "Sub-Brand": 'BRAND'
    }
        
    selected_option = st.sidebar.selectbox("Choose a dataset", ["State", "Brand", "Brand Item", "State Brandwise","Sub-Brand"], key='maindataset_sidebar_unique')
    st.title(titles[selected_option])
    st.write("")
    file_path = file_paths[selected_option]
    parameter1 = parameters1[selected_option]
    parameter2 = parameters2[selected_option]
    df = pd.DataFrame()
    if selected_option == 'State Brandwise' or selected_option == 'Brand Item':
        df, unique_array = load_data(file_path,parameter1, parameter2)
        selected_state = st.sidebar.selectbox('Select:', unique_array,key='statebrandwise') 
        data = df[df[parameter2] == selected_state]
    else:
        data = load_data(file_path,parameter1, parameter2)
    l_sec, r_sec = st.columns([3, 5])
    with r_sec:
        #hist
        st.sidebar.markdown('<a href="#sales-distribution-analysis" style="text-decoration: none; font-size: 24px; font-weight:bold;">Sales Distribution Analysis</a>', unsafe_allow_html=True)
        y_data_line_option = st.sidebar.selectbox("Choose a parameter: ", ['Qty(S1)', 'Qty(S2)', 'Abs diff in qty', '%Qty1','Amount(S1)', 'Amount(s2)', 'Abs diff in amt', 'Amount(1)%'], key='line_chart')
        st.markdown('<h2 id="sales-distribution-analysis">SALES DISTRIBUTION ANALYSIS</h2>', unsafe_allow_html=True)
        top7, bot7 =  plot_histogram(data, y_data_line_option, parameter1)
    with l_sec:
        print_blank_lines(1)
        display_totals_and_means(data)
        col1, col2, col3, col4 = st.columns([1,7,7,1])
        with col1:
            st.write("")
        with col4:
            st.write("")
        with col2:
            st.markdown("<p style='text-align: center; font-weight: bold; font-size: 18px'>TOP 7</p>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; justify-content: right; align-items: right;'><style> .dataframe { margin-left: auto; margin-right: auto; } </style>", unsafe_allow_html=True)
            st.write(top7)
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<p style='text-align: center; font-weight: bold; font-size: 18px'>BOTTOM 7</p>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; justify-content: right; align-items: right;'><style> .dataframe { margin-left: auto; margin-right: auto; } </style>", unsafe_allow_html=True)
            st.write(bot7)
            st.markdown("</div>", unsafe_allow_html=True)

    print_blank_lines(4)
    left_sec, right_sec = st.columns([3, 2])
    with left_sec:
        #line
        st.sidebar.markdown('<a href="#trends-analysis" style="text-decoration: none; font-size: 24px; font-weight:bold;">Trend Analysis</a>', unsafe_allow_html=True)
        line_chart_option = st.sidebar.selectbox(
            "Choose a Line Chart Analysis type:",
            ['Qty1 vs Qty2', 'Amt1 vs Amt2', 'Qty1% vs Qty2%', 'Amt1% vs Amt2%', 'QtyAbsDiff vs AmtAbsdiff', 'F vs V'],
        key='line_chart_option')
        plot_height1 = st.sidebar.slider("Choose Line Chart Height", 400, 800, 600, key='line_chart_height')
        st.markdown('<h2 id="trends-analysis">TRENDS ANALYSIS</h2>', unsafe_allow_html=True)
        plot_line_chart(data, line_chart_option, parameter1, plot_height1)
    with right_sec:
        #DONUT
        st.sidebar.markdown('<a href="#segment-analysis" style="text-decoration: none; font-size: 24px; font-weight:bold;">Segment Analysis</a>', unsafe_allow_html=True)
        st.markdown('<h2 id="segment-analysis">SEGMENT ANALYSIS</h2>', unsafe_allow_html=True)
        donut_option = st.sidebar.selectbox("Choose a parameter: ", ['Market Share last year in Q1', 'Market Share this year in Q1', 'Revenue Contribution last year', 'Revenue Contribution this year', 'Growth in Quantity', 'Growth in Revenue'], key='donut')
        plot_donut_chart(data, parameter1, donut_option)
    
    print_blank_lines(2)
    #MULTIBAR 
    st.sidebar.markdown('<a href="#multi-bar-chart" style="text-decoration: none; font-size: 24px; font-weight:bold;">Comparative Performance Analysis</a>', unsafe_allow_html=True)
    comparison_type = st.sidebar.selectbox("Choose a BUSINESS ANALYSIS type: ", ["Fluctuation in Volume", "Volatility in Revenue", "Pareto Analysis", "Variance Analysis"], key='multibar')
    st.markdown('<div id="multi-bar-chart"></div>', unsafe_allow_html=True)
    st.markdown('<h2>COMPARITIVE PERFORMANCE ANALYSIS</h2>', unsafe_allow_html=True)
    plot_multi_bar_chart(data, comparison_type, parameter1)
    
    #TABLE
    print_blank_lines(4)
    last_columns = ['Qty(S1)', 'Volume1_%total', 'Qty(S2)', 'Volume2_%total', 'Abs diff in qty', '%Qty1', 
        'Amount(S1)', 'Revenue1_%total', 'Amount(s2)', 'Revenue2_%total', 'Abs diff in amt', 'Amount(1)%']
    st.sidebar.markdown('<a href="#sales-performance-analysis" style="text-decoration: none; font-size: 24px; font-weight:bold;">Sales Performance Analysis</a>', unsafe_allow_html=True)
    classification = st.sidebar.selectbox("Select a parameter:", last_columns, key='combinedTable')
    data_sorted = data.sort_values(by=classification, ascending=False)
    combined_html_table = generate_html_table(data_sorted, parameter1,parameter2)
    st.markdown('<h2 id="sales-performance-analysis">SALES PERFORMANCE ANALYSIS</h2>', unsafe_allow_html=True)
    print_blank_lines(2)
    st.markdown(combined_html_table, unsafe_allow_html=True)
    
    #NARRATIVE
    print_blank_lines(4)
    st.markdown('<h2 id="narrative">NARRATIVE</h2>', unsafe_allow_html=True)
    print_blank_lines(2)
    st.sidebar.markdown('<a href="#narrative" style="text-decoration: none; font-size: 24px; font-weight:bold;">Narrative</a>', unsafe_allow_html=True)
    narrative(data, parameter1)
    
if __name__ == "__main__":
    main()