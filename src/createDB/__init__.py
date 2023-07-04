from createDB.objeto_um import Um
from createDB.connectionDB import connectDB
import pyodbc
import streamlit as st
import pandas as pd

Um.imprimeUm()

BD = {
    "EstoqueBD": "produto, quantidade",
    "RomaneioBD": "produto, peso_total, desc_item, TAG, num_NF, data_embarque, quantidade, num_volume, local",
    "LocaINT": "produto",
    "FornecedorINT": "produto",
    
}

INT = {
    "EstoqueINT": "produto",
    "RomaneioINT": "produto",
    "LocaINT": "produto",
    "FornecedorINT": "produto",
}

RENAME = {
    "Estoque": {"produto":"Produto", "quantidade":"Quantidade"},
    "Romaneio": {"produto":"Produto","peso_total":"Peso Total","desc_item":"Descrição do item","TAG":"TAG","num_NF":"Numero da Nota Fiscal","data_embarque":"Ultima data atualizada","quantidade":"Quantidade","num_volume":"Numero do Volume","local":"Local"},
    "Local": {"titulo_local":"Título do Local", "status":"Status", "data_utilizacao": "Data de Utilização", "espaco_faltante":"Espaço Faltante"},
    "Fornecedor": {"nome_fornecedor":"Nome do Fornecedor", "num_fornecedor":"Número do Fornecedor"},
}



def show(name, connection, tabela, ponteiro):
    # Função para exibir os dados
    def exibir_dados():
        query = f"SELECT {BD[name]} FROM {tabela}"
        data = pd.read_sql(query, connection).rename(columns=RENAME[name])
        st.subheader("Dados do Estoque")
        st.table(data)
        connection.close()

    # Função para adicionar um novo item
    def adicionar_item():
        st.subheader("Adicionar Item")
        produto = st.text_input("Nome do Produto")
        quantidade = st.number_input("Quantidade", min_value=0)
        if st.button("Adicionar"):
            cursor = connection.cursor()
            cursor.execute(
                f"""INSERT INTO {tabela} ({BD['EstoqueBD']}) VALUES (?, ?)""",
                (produto, quantidade),
            )
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Item adicionado com sucesso.")

    # Função para atualizar um item existente
    def atualizar_item():
        st.subheader("Atualizar Item")
        cursor = connection.cursor()
        cursor.execute(f"SELECT id, {ponteiro} FROM {tabela}")
        items = cursor.fetchall()
        item_ids = [str(item[0]) + ": " + item[1] for item in items]
        item_id = st.selectbox("Selecione o Item a ser Atualizado", item_ids)
        produto = st.text_input("Novo nome do Produto")
        quantidade = st.number_input("Nova Quantidade", min_value=0)
        if st.button("Atualizar"):
            item_id = item_id.split(":")[0]
            cursor.execute(
                f"UPDATE {tabela} SET {ponteiro} = ?, quantidade = ? WHERE id = ?",
                (produto, quantidade, item_id),
            )
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Item atualizado com sucesso.")

    # Função para remover um item
    def remover_item():
        st.subheader("Remover Item")
        cursor = connection.cursor()
        cursor.execute(f"SELECT id, {ponteiro} FROM {tabela}")
        items = cursor.fetchall()
        item_ids = [str(item[0]) + ": " + item[1] for item in items]
        item_id = st.selectbox("Selecione o Item a ser Removido", item_ids)
        if st.button("Remover"):
            item_id = item_id.split(":")[0]
            cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (item_id,))
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Item removido com sucesso.")
