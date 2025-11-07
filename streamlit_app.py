import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Painel de Monitoramento", layout="centered")

# Inicializa estado
if "etapa" not in st.session_state:
    st.session_state["etapa"] = "inicio"

st.title("Bem-vindo ao Painel de Monitoramento!")

def extrair_bairro(endereco):
    if pd.isna(endereco):
        return "Desconhecido"
    try:
        match_ponto = re.search(r"\.\s([^.,-]+), Porto Alegre - RS", endereco)
        if match_ponto:
            return match_ponto.group(1).strip()
        match_hifen = re.search(r" - ([^.,]+), Porto Alegre - RS", endereco)
        if match_hifen:
            return match_hifen.group(1).strip()
    except:
        return "Desconhecido"
    return "Desconhecido"

# Upload dos arquivos
hipertensos_file = st.file_uploader("📄 Insira a planilha de hipertensos", type=["xlsx"])
diabeticos_file = st.file_uploader("📄 Insira a planilha de diabéticos", type=["xlsx"])

if st.session_state["etapa"] == "inicio":
    if hipertensos_file and diabeticos_file:
        df_hipertensos = pd.read_excel(hipertensos_file, engine="openpyxl")
        df_diabeticos = pd.read_excel(diabeticos_file, engine="openpyxl")

        st.write("### Visualização inicial dos dados:")
        st.write("#### Hipertensos")
        st.dataframe(df_hipertensos.head())
        st.write("#### Diabéticos")
        st.dataframe(df_diabeticos.head())

        confirmar = st.radio("Você confirma que os dados estão corretos?", ["Não", "Sim"])

        if confirmar == "Sim":
            if st.button("Ir para os gráficos"):
                # Salva os DataFrames no estado
                df_hipertensos["Tipo"] = "Hipertenso"
                df_diabeticos["Tipo"] = "Diabético"
                st.session_state["df_total"] = pd.concat([df_hipertensos, df_diabeticos], ignore_index=True)
                st.session_state["etapa"] = "graficos"
else:
    # Etapa dos gráficos
    df_total = st.session_state["df_total"]

    # Usa coluna correta para endereço
    col_endereco = df_total.columns[1]
    df_total.rename(columns={col_endereco: "Endereço"}, inplace=True)
    df_total["Bairro"] = df_total["Endereço"].apply(extrair_bairro)

    # Converter coluna de data para datetime
    df_total["Último Atendimento"] = pd.to_datetime(df_total[df_total.columns[2]], errors="coerce", dayfirst=True)

    # Calcular indicadores
    hoje = pd.Timestamp.today()
    df_total["Dias desde atendimento"] = (hoje - df_total["Último Atendimento"]).dt.days

    total_hipertensos = len(df_total[df_total["Tipo"] == "Hipertenso"])
    total_diabeticos = len(df_total[df_total["Tipo"] == "Diabético"])
    total_pacientes = len(df_total)

    sem_atendimento_6m = len(df_total[df_total["Dias desde atendimento"] > 180])
    percentual_sem_6m = (sem_atendimento_6m / total_pacientes) * 100 if total_pacientes > 0 else 0
    media_dias = df_total["Dias desde atendimento"].mean() if total_pacientes > 0 else 0

    # Exibir indicadores
    st.write("### Indicadores Iniciais")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de pacientes", total_pacientes)
    col2.metric("Hipertensos", total_hipertensos)
    col3.metric("Diabéticos", total_diabeticos)

    col4, col5 = st.columns(2)
    col4.metric("Sem atendimento > 6 meses", f"{percentual_sem_6m:.1f}%")
    col5.metric("Média de dias desde último atendimento", f"{media_dias:.0f} dias")

    # Validação simples
    if percentual_sem_6m > 50:
        st.warning("⚠️ Mais de 50% dos pacientes estão sem atendimento há mais de 6 meses!")
    if media_dias > 180:
        st.warning("⚠️ Média de dias desde último atendimento está acima do esperado (180 dias).")

    # Filtro múltiplo
    st.write("### Dashboard")
    tipos_selecionados = st.multiselect(
        "Selecione os tipos de pacientes:",
        ["Hipertenso", "Diabético"],
        default=["Hipertenso", "Diabético"]
    )

    if tipos_selecionados:
        df_filtrado = df_total[df_total["Tipo"].isin(tipos_selecionados)]
        if not df_filtrado.empty:
            # Contagem por bairro
            contagem = df_filtrado["Bairro"].value_counts().reset_index()
            contagem.columns = ["Bairro", "Quantidade"]

            # Gráfico
            fig = px.bar(contagem, x="Bairro", y="Quantidade", title="Distribuição de pacientes por bairro")
            st.plotly_chart(fig)

            # Tabela detalhada
            st.write("### Pacientes filtrados")
            st.dataframe(df_filtrado)
        else:
            st.warning("⚠️ Nenhum dado disponível para os tipos selecionados.")
    else:
        st.warning("⚠️ Selecione pelo menos um tipo para visualizar o gráfico.")