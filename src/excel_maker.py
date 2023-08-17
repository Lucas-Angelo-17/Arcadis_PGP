import streamlit as st
import pandas as pd
import io

def gerar_planilha():
    # Dados fictícios para a planilha
    dados = {
        'CODIGO': [],
        'NOME': [],
        'QUANTIDADE': [],
    }

    # Criando o DataFrame a partir dos dados
    df = pd.DataFrame(dados)

    return df

def excel_maker():

    # Gerar a planilha
    df = gerar_planilha()

    # Criando o arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, engine='utf-8')

    # Configurando o buffer para a posição inicial
    output.seek(0)

    # Exibindo o link de download
    st.download_button(label='Planilha de exemplo', data=output, file_name='planilha_exemplo.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

