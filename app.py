import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# Set page configuration

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.write(' ')

with col2:
    st.write(' ')

with col3:
    st.image("https://upload.wikimedia.org/wikipedia/id/thumb/b/bc/Logo_Universitas_Sriwijaya.svg/1008px-Logo_Universitas_Sriwijaya.svg.png?20240818010951")
with col4:
    #st.write('Unsri PTNBH')
    st.subheader("Unsri PTNBH")
with col5:
    st.write(' ')
with col6:
    st.write(' ')

st.title("Analisis Pencapaian CPL")

# Add input fields for Program Studi and Fakultas
program_studi = st.text_input("Masukkan Nama Program Studi", "XXX")
fakultas = st.text_input("Masukkan Nama Fakultas", "XYZ")

st.subheader(f"Program Studi: :blue[{program_studi}] :office:  Fakultas: :red[{fakultas}]")

# --- Load Configuration and Data ---
@st.cache_data
def load_data(cpl_config_path, student_data_path):
    df_cpl_mapping = pd.read_excel(cpl_config_path, sheet_name='CPK_Mapping')
    df_sks_weights = pd.read_excel(cpl_config_path, sheet_name='sks_Bobot')
    df_mahasiswa_nilai = pd.read_excel(student_data_path)
    return df_cpl_mapping, df_sks_weights, df_mahasiswa_nilai

# Adjust paths if necessary based on where the script is run
cpl_config_path = 'cpl_analysis_app/cpl_config.xlsx'
student_data_path = 'cpl_analysis_app/data_nilai_mahasiswa.xlsx'

if not os.path.exists(cpl_config_path):
    st.error(f"Error: Configuration file not found at {cpl_config_path}")
    st.stop()
if not os.path.exists(student_data_path):
    st.error(f"Error: Student data file not found at {student_data_path}")
    st.stop()

df_cpl_mapping, df_sks_weights, df_mahasiswa_nilai = load_data(cpl_config_path, student_data_path)

st.header("Data Input :")
st.subheader("Pemetaan CPL ke Sub-CPMK")
st.dataframe(df_cpl_mapping)
st.subheader("Bobot sks Mata Kuliah")
st.dataframe(df_sks_weights)
st.subheader("Nilai Mahasiswa")
st.dataframe(df_mahasiswa_nilai)

# --- Calculate CPL Achievements ---
st.header("Perhitungan Pencapaian CPL :")

cpl_achievements_external = {}
for index, row in df_cpl_mapping.iterrows():
    cpl = row['CPL']
    sub_cpmks_str = row['Sub_CPMKs']
    sub_cpmks = [sub_cpmk.strip() for sub_cpmk in sub_cpmks_str.split(',')]

    weighted_scores_list = []
    total_sks_for_cpl = 0

    for sub_cpmk in sub_cpmks:
        if sub_cpmk in df_mahasiswa_nilai.columns:
            mk_prefix = sub_cpmk.split('_')[0]
            sks_row = df_sks_weights[df_sks_weights['Kode_MK'] == mk_prefix]
            if not sks_row.empty:
                sks = sks_row['sks'].iloc[0]
                if sks > 0:
                    weighted_scores_list.append(df_mahasiswa_nilai[sub_cpmk] * sks)
                    total_sks_for_cpl += sks
            else:
                st.warning(f"Warning: SKS weight not found for course prefix '{mk_prefix}'.")
        else:
            st.warning(f"Warning: Sub_CPMK column '{sub_cpmk}' not found in student data.")

    if weighted_scores_list and total_sks_for_cpl > 0:
        sum_weighted_scores = sum(weighted_scores_list)
        cpl_achievements_external[cpl] = sum_weighted_scores / total_sks_for_cpl
    else:
        cpl_achievements_external[cpl] = pd.Series([0] * len(df_mahasiswa_nilai))

# Calculate the average achievement for each CPL across all students
average_cpl_achievements_external = {cpl: scores.mean() for cpl, scores in cpl_achievements_external.items()}

# Convert to a Pandas Series for easier handling and display
average_cpl_achievements_series_external = pd.Series(average_cpl_achievements_external, name="Rata-rata")

st.subheader("Rata-rata Pencapaian CPL Program Studi")
st.dataframe(average_cpl_achievements_series_external)

# --- Visualize Average CPL Achievements ---
#st.header("Visualisasi Rata-rata Pencapaian CPL")

cpl_categories_external = list(average_cpl_achievements_series_external.index)

fig_radar_avg = go.Figure()

fig_radar_avg.add_trace(go.Scatterpolar(
    r=average_cpl_achievements_series_external.values,
    theta=cpl_categories_external,
    fill='toself',
    name='Rata-rata Pencapaian CPL'
))

fig_radar_avg.update_layout(
    title='Rata-rata Pencapaian CPL Program Studi',
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    )
)

st.plotly_chart(fig_radar_avg)

# --- Analyze CPL Achievement per Student ---
st.subheader("Analisis Pencapaian CPL per Mahasiswa")

# Calculate CPL achievements for each student
cpl_achievements_per_student = {}

for index, row in df_cpl_mapping.iterrows():
    cpl = row['CPL']
    sub_cpmks_str = row['Sub_CPMKs']
    sub_cpmks = [sub_cpmk.strip() for sub_cpmk in sub_cpmks_str.split(',')]

    weighted_scores_list = []
    total_sks_for_cpl = 0

    for sub_cpmk in sub_cpmks:
        if sub_cpmk in df_mahasiswa_nilai.columns:
            mk_prefix = sub_cpmk.split('_')[0]
            sks_row = df_sks_weights[df_sks_weights['Kode_MK'] == mk_prefix]
            if not sks_row.empty:
                sks = sks_row['sks'].iloc[0]
                if sks > 0:
                    weighted_scores_list.append(df_mahasiswa_nilai[sub_cpmk] * sks)
                    total_sks_for_cpl += sks
            # else: Warning already handled in the previous loop
        # else: Warning already handled in the previous loop


    if weighted_scores_list and total_sks_for_cpl > 0:
        cpl_achievements_per_student[cpl] = sum(weighted_scores_list) / total_sks_for_cpl
    else:
        cpl_achievements_per_student[cpl] = pd.Series([0] * len(df_mahasiswa_nilai))

# Convert the dictionary of Series to a DataFrame
df_cpl_achievements_per_student = pd.DataFrame(cpl_achievements_per_student)

# Add 'Nama Mahasiswa' and 'NIM' for identification
df_cpl_achievements_per_student.insert(0, 'NIM', df_mahasiswa_nilai['NIM'])
df_cpl_achievements_per_student.insert(0, 'Nama Mahasiswa', df_mahasiswa_nilai['Nama Mahasiswa'])

#st.subheader("Pencapaian CPL per Mahasiswa")
st.dataframe(df_cpl_achievements_per_student)

# --- Visualize CPL Achievement per Student (Box Plot) ---
#st.header("Visualisasi Sebaran Pencapaian CPL per Mahasiswa")

# Melt the DataFrame containing CPL achievements per student to long format for easier plotting with Plotly Express
df_melted_cpl_achievements = df_cpl_achievements_per_student.melt(
    id_vars=['Nama Mahasiswa', 'NIM'],
    var_name='CPL',
    value_name='Pencapaian CPL'
)

# Create box plots for each CPL with individual points overlaid
fig_box_cpl_student = px.box(
    df_melted_cpl_achievements,
    x='CPL',
    y='Pencapaian CPL',
    title='Sebaran Pencapaian CPL per Mahasiswa',
    points="all", # Show all points
    hover_data=['Nama Mahasiswa', 'NIM', 'Pencapaian CPL'] # Show student details on hover
)

fig_box_cpl_student.update_layout(yaxis_range=[0, 100])

st.plotly_chart(fig_box_cpl_student)

# --- Identify Low Achieving Students ---
st.header("Identifikasi Mahasiswa dengan Pencapaian CPL Rendah :")

# Define a threshold for low achievement (e.g., below 80)
threshold = st.slider("Pilih Ambang Batas Pencapaian Rendah", 0, 100, 80)

# Identify students with low achievement for each CPL
low_achievers = {}
all_low_achievers_nims_list = []

st.subheader(f"Mahasiswa dengan Pencapaian CPL di Bawah Ambang Batas ({threshold}):")
for cpl in average_cpl_achievements_series_external.index:
    low_achieving_students = df_cpl_achievements_per_student[df_cpl_achievements_per_student[cpl] < threshold].copy()
    if not low_achieving_students.empty:
        low_achievers[cpl] = low_achieving_students[['Nama Mahasiswa', 'NIM', cpl]]
        all_low_achievers_nims_list.extend(low_achieving_students['NIM'].tolist())
        st.write(f"--- {cpl} ---")
        st.dataframe(low_achievers[cpl])
    else:
        st.write(f"Tidak ada mahasiswa dengan pencapaian di bawah ambang batas untuk {cpl}.")

# Combine all low-achieving students from the dictionary into a single DataFrame (removing duplicates)
all_low_achievers_nims = pd.DataFrame({'NIM': list(set(all_low_achievers_nims_list))})


# --- Deep Dive Analysis for Low Achievers ---
st.header("Analisis Lebih Lanjut Mahasiswa dengan Pencapaian CPL Rendah :")

if not all_low_achievers_nims.empty:
    # Filter the main student achievement DataFrame to get the full CPL achievements for these students
    df_low_achievers_details = df_cpl_achievements_per_student[
        df_cpl_achievements_per_student['NIM'].isin(all_low_achievers_nims['NIM'])
    ]

    st.subheader("Detail Pencapaian CPL untuk Mahasiswa dengan Pencapaian Rendah Paling Sedikit di Satu CPL:")
    st.dataframe(df_low_achievers_details)

    # --- Visualize CPL Achievement for Low Achievers (Radar Chart) ---
    #st.subheader("Visualisasi Pencapaian CPL untuk Mahasiswa Berkinerja Rendah")

    cpl_categories = list(average_cpl_achievements_series_external.index)

    fig_radar_low_achievers = go.Figure()

    for index, row in df_low_achievers_details.iterrows():
        fig_radar_low_achievers.add_trace(go.Scatterpolar(
            r=row[cpl_categories].values,
            theta=cpl_categories,
            fill='toself',
            name=row['Nama Mahasiswa']
        ))

    fig_radar_low_achievers.update_layout(
        title='Pencapaian CPL per Mahasiswa dengan Pencapaian Rendah',
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True
    )

    st.plotly_chart(fig_radar_low_achievers)

    # --- Analyze Sub-CPMK Contribution to Low Achievement ---
    st.subheader("Analisis Pencapaian CPL Rendah:")

    #st.subheader("Analisis Nilai Sub-CPMK untuk Mahasiswa dengan Pencapaian CPL Rendah:")

    for cpl, students_df in low_achievers.items():
        if not students_df.empty:
            st.write(f"--- Analisis untuk {cpl} (Mahasiswa dengan skor CPL < {threshold}) ---")

            cpl_mapping_row = df_cpl_mapping[df_cpl_mapping['CPL'] == cpl]
            if not cpl_mapping_row.empty:
                sub_cpmks_str = cpl_mapping_row['Sub_CPMKs'].iloc[0]
                relevant_sub_cpmks = [sub_cpmk.strip() for sub_cpmk in sub_cpmks_str.split(',')]

                columns_to_display = ['Nama Mahasiswa', 'NIM'] + relevant_sub_cpmks
                columns_to_display = [col for col in columns_to_display if col in df_mahasiswa_nilai.columns]

                low_achievers_sub_cpmk_data = df_mahasiswa_nilai[
                    df_mahasiswa_nilai['NIM'].isin(students_df['NIM'])
                ][columns_to_display]

                if not low_achievers_sub_cpmk_data.empty:
                    st.dataframe(low_achievers_sub_cpmk_data)
                else:
                    st.write(f"No Sub-CPMK data available for relevant columns for low achievers in {cpl}.")
            else:
                st.write(f"No Sub-CPMK mapping found for {cpl}.")

        # --- Identify Critical Courses ---
    st.header("Identifikasi Mata Kuliah Kritis :")

    st.subheader("Identifikasi Mata Kuliah Kritis berdasarkan Nilai Rata-rata Sub-CPMK:")

    difference_threshold = st.slider("Pilih Ambang Batas Perbedaan Rata-rata untuk Mata Kuliah Kritis", 0, 30, 10)

    for cpl, students_df in low_achievers.items():
        if not students_df.empty:
            st.write(f"--- Mata Kuliah Kritis untuk {cpl} ---")

            cpl_mapping_row = df_cpl_mapping[df_cpl_mapping['CPL'] == cpl]
            if not cpl_mapping_row.empty:
                sub_cpmks_str = cpl_mapping_row['Sub_CPMKs'].iloc[0]
                relevant_sub_cpmks = [sub_cpmk.strip() for sub_cpmk in sub_cpmks_str.split(',')]

                low_achievers_sub_cpmk_data = df_mahasiswa_nilai[
                    df_mahasiswa_nilai['NIM'].isin(students_df['NIM'])
                ][relevant_sub_cpmks]

                if not low_achievers_sub_cpmk_data.empty:
                    average_low_achievers_sub_cpmk_scores = low_achievers_sub_cpmk_data.mean()
                    overall_average_sub_cpmk_scores = df_mahasiswa_nilai[relevant_sub_cpmks].mean()

                    comparison_df = pd.DataFrame({
                        'Rata-rata Mahasiswa Rendah': average_low_achievers_sub_cpmk_scores,
                        'Rata-rata Keseluruhan': overall_average_sub_cpmk_scores
                    })

                    comparison_df['Perbedaan Rata-rata'] = comparison_df['Rata-rata Keseluruhan'] - comparison_df['Rata-rata Mahasiswa Rendah']
                    comparison_df_sorted = comparison_df.sort_values(by='Perbedaan Rata-rata', ascending=False)
                    comparison_df_sorted['Mata Kuliah'] = comparison_df_sorted.index.str.split('_').str[0]

                    st.write("Perbandingan Rata-rata Nilai Sub-CPMK dan Mata Kuliah Terkait:")
                    st.dataframe(comparison_df_sorted)

                    critical_sub_cpmks = comparison_df_sorted[comparison_df_sorted['Perbedaan Rata-rata'] > difference_threshold]

                    if not critical_sub_cpmks.empty:
                        st.write(f"Sub-CPMK Kritis (Perbedaan Rata-rata > {difference_threshold}):")
                        st.dataframe(critical_sub_cpmks)

                        critical_courses = critical_sub_cpmks['Mata Kuliah'].unique()
                        st.write(f"Mata Kuliah Kritis yang Teridentifikasi untuk {cpl}:")
                        for course in critical_courses:
                            st.write(f"- {course}")
                    else:
                        st.write("Tidak ada Sub-CPMK yang teridentifikasi kritis berdasarkan ambang batas perbedaan rata-rata.")

                else:
                     st.write(f"No Sub-CPMK data available for relevant columns for low achievers in {cpl}.")
            else:
                st.write(f"No Sub-CPMK mapping found for {cpl}.")
else:
    st.write("Tidak ada mahasiswa yang teridentifikasi memiliki pencapaian rendah di setidaknya satu CPL.")


# --- Analyze Specific Course ---
st.header("Analisis Lebih Lanjut Mata Kuliah Spesifik :")

# Allow user to select a course for detailed analysis
course_options = df_sks_weights['Kode_MK'].tolist()
selected_course_prefix = st.selectbox("Pilih Mata Kuliah untuk Analisis Lebih Lanjut :", course_options)

if selected_course_prefix:
    st.write(f"Mata kuliah yang dipilih untuk analisis: {selected_course_prefix}")

    # Identify relevant Sub-CPMKs for the selected course
    relevant_cpl_mappings = df_cpl_mapping[df_cpl_mapping['Sub_CPMKs'].str.contains(selected_course_prefix)]
    relevant_sub_cpmks = []
    for index, row in relevant_cpl_mappings.iterrows():
        sub_cpmks_str = row['Sub_CPMKs']
        sub_cpmks = [sub_cpmk.strip() for sub_cpmk in sub_cpmks_str.split(',')]
        for sub_cpmk in sub_cpmks:
            if sub_cpmk.startswith(selected_course_prefix + '_'):
                relevant_sub_cpmks.append(sub_cpmk)
    relevant_sub_cpmks = list(set(relevant_sub_cpmks))

    st.subheader(f"Sub-CPMKs yang terkait dengan {selected_course_prefix}:")
    st.write(relevant_sub_cpmks)

    if relevant_sub_cpmks:
        # Filter student data for the selected Sub-CPMKs
        columns_to_select = ['Nama Mahasiswa', 'NIM'] + relevant_sub_cpmks
        df_selected_course_nilai = df_mahasiswa_nilai[columns_to_select]

        st.subheader("Data Nilai Sub-CPMK Mata Kuliah Terpilih")
        st.dataframe(df_selected_course_nilai)

        # Calculate descriptive statistics
        st.subheader("Statistik Deskriptif Nilai Sub-CPMK Mata Kuliah Terpilih")
        sub_cpmk_data = df_selected_course_nilai[relevant_sub_cpmks]
        sub_cpmk_descriptive_stats = sub_cpmk_data.describe()
        st.dataframe(sub_cpmk_descriptive_stats)

        # Identify low-achieving students at the Sub-CPMK level for the selected course
        st.subheader(f"Mahasiswa dengan Nilai Sub-CPMK di Bawah Ambang Batas ({threshold}) di {selected_course_prefix}:")
        low_achievers_sub_cpmk = {}
        for sub_cpmk in relevant_sub_cpmks:
            low_achieving_students_sub_cpmk = df_selected_course_nilai[
                df_selected_course_nilai[sub_cpmk] < threshold
            ].copy()
            if not low_achieving_students_sub_cpmk.empty:
                low_achievers_sub_cpmk[sub_cpmk] = low_achieving_students_sub_cpmk[['Nama Mahasiswa', 'NIM', sub_cpmk]]
                st.write(f"--- {sub_cpmk} ---")
                st.dataframe(low_achievers_sub_cpmk[sub_cpmk])
            else:
                st.write(f"Tidak ada mahasiswa dengan nilai di bawah ambang batas untuk {sub_cpmk}.")

        # Visualize Sub-CPMK scores for the selected course
        st.subheader(f"Sebaran Nilai Sub-CPMK untuk {selected_course_prefix}")
        df_melted_sub_cpmk_nilai = df_selected_course_nilai.melt(
            id_vars=['Nama Mahasiswa', 'NIM'],
            var_name='Sub-CPMK',
            value_name='Nilai Sub-CPMK'
        )
        fig_scatter_sub_cpmk = px.scatter(
            df_melted_sub_cpmk_nilai,
            x='Sub-CPMK',
            y='Nilai Sub-CPMK',
            color='Nama Mahasiswa',
            hover_data=['NIM', 'Nama Mahasiswa', 'Nilai Sub-CPMK'],
            title=f'Sebaran Nilai Sub-CPMK per Mahasiswa untuk {selected_course_prefix}'
        )
        fig_scatter_sub_cpmk.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig_scatter_sub_cpmk)

    else:
        st.write(f"Tidak ada Sub-CPMK yang terkait dengan mata kuliah '{selected_course_prefix}'.")
