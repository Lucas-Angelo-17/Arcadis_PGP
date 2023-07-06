import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit_authenticator as stauth
from pathlib import Path
import pickle
import pyodbc
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from streamlit_option_menu import option_menu
import urllib.request

#Anotação tlvez nescessárias
#convert(VARCHAR, data_embarque, 103) as 'data_embarque'
RENAME = {
    "Estoque": {"produto":"Produto", "quantidade":"Quantidade"},
    "Romaneio": {"item":"Item","fornecedor":"Fornecedor","pedido_compra":"Pedido de Compra","TAG":"TAG","num_NF":"Numero da Nota Fiscal","num_desenho":"Número do desenho","quantidade":"Quantidade","num_volume_eq":"Numero do Volume","local":"Local", "desc_es":"Descrição (Estrutura Metálica)", "desc_material":"Descrição do Material", "area":"Área", "peso":"Peso"},
    "Local": {"titulo_local":"Título do Local", "status":"Status", "data_utilizacao": "Data de Utilização", "espaco_faltante":"Espaço Faltante"},
    "Fornecedor": {"nome_fornecedor":"Nome do Fornecedor", "num_fornecedor":"Número do Fornecedor"},
}


# Conectar ao banco de dados MySQL
def conectar_bd():
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=Arcappbr002,1433;"
        "Database=Dir_Mineracao;"
        "UID=dir_mineracao;"
        "PWD=RMib52Qk;"
        # "Trusted_Connection=yes;"
    )
    connection = pyodbc.connect(
        dados_conexao
    )
    return connection

def criar_tabelaAll(tabela, createTable):
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute(
        f"""
        IF NOT EXISTS(SELECT * FROM sys.tables WHERE name = '{tabela}')
        BEGIN
            {createTable}
        END
        """
    )
    connection.commit()
    cursor.close()
    connection.close()

st.set_page_config(
    page_title="SGA Arcadis",
    page_icon="images/Arcadis-Symbol.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Função para exibir os dados
def exibir_dados():
    connection = conectar_bd()
    query = "SELECT produto, quantidade FROM estoque"
    data = pd.read_sql(query, connection).rename(columns=RENAME["Estoque"])
    st.subheader("Dados do Estoque")
    st.table(data)
    connection.close()


# Função para adicionar um novo item
def adicionar_item():
    select_tipo = st.selectbox("Tipos de Recebimento", ["LM's", "Equipamentos", "Estrutura Metálica"])
    if(select_tipo == "LM's"):
        st.subheader("Adicionar LM's")
        produto = st.text_input("Nome do Produto")
        quantidade = st.number_input("Quantidade", min_value=0)

        if st.button("Adicionar"):
            connection = conectar_bd()
            cursor = connection.cursor()
            cursor.execute(
                '''INSERT INTO estoque (produto, quantidade) VALUES (?, ?)''',
                (produto, quantidade),
            )
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Item adicionado com sucesso.")

    if(select_tipo == "Equipamentos"):
        st.subheader("Adicionar Equipamentos")
        produto = st.text_input("Nome do Produto")
        quantidade = st.number_input("Quantidade", min_value=0)
        uploaded_file = st.file_uploader("Packing List")
        if uploaded_file is not None :
            planilha = pd.read_excel(uploaded_file)
            for row in planilha.to_dict(orient="records"):
                print("AQUIIIIIIIIIIIII!!!!!!!!!!!!!!")
                print(row)
                cursor.execute(f"INSERT INTO mercado (produto, quantidade, valor) VALUES (?, ?, ?)",
                            row['Produto'], row['quantidade'], row['preço'])
                connection.commit()

        if st.button("Adicionar"):
            connection = conectar_bd()
            cursor = connection.cursor()
            cursor.execute(
                '''INSERT INTO estoque (produto, quantidade) VALUES (?, ?)''',
                (produto, quantidade),
            )
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Item adicionado com sucesso.")


# Função para atualizar um item existente
def atualizar_item():
    st.subheader("Atualizar Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, produto FROM estoque")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Atualizado", item_ids)
    produto = st.text_input("Novo nome do Produto")
    quantidade = st.number_input("Nova Quantidade", min_value=0)
    if st.button("Atualizar"):
        item_id = item_id.split(":")[0]
        cursor.execute(
            "UPDATE estoque SET produto = ?, quantidade = ? WHERE id = ?",
            (produto, quantidade, item_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item atualizado com sucesso.")


# Função para remover um item
def remover_item():
    st.subheader("Remover Item")
    col1, col2= st.columns(2)
    with col1:
        item_id = st.selectbox("Dar baixa", exibir_itens("packing_list", "desc_material"))
    with col2:
        #Pegar a lista de Colaboradores
        colaborador = st.selectbox("Colaborador", exibir_itens("Colaborador", "nome_colaborador"))
    #Pegar o lugar de onde tava e atualiza ele


    connection = conectar_bd()
    cursor = connection.cursor()
    query_romaneio2 = f"WITH BannedCTE AS (SELECT local FROM packing_list WHERE packing_list.desc_material = {item_id}) select * from BannedCTE ;"
    
    query_romaneio = f'''SELECT local FROM packing_list WHERE desc_material = "{item_id}"'''
    data = pd.read_sql(query_romaneio, connection)
    newLocal = st.text_input(placeholder=data)

    if st.button("Remover"):

        item_id = item_id.split(":")[0]
        cursor.execute("UPDATE local FROM estoque WHERE id = ?", (newLocal))
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item removido com sucesso.")



# ________________Conexão Romaneio BD____________________________


# Função para exibir os dados
def exibir_dados2():
    connection = conectar_bd()
    query_romaneio = "SELECT num_NF, item, fornecedor, pedido_compra FROM romaneio"
    data = pd.read_sql(query_romaneio, connection).rename(columns=RENAME["Romaneio"])
    st.subheader("Dados do Romaneio")
    options_builder = GridOptionsBuilder.from_dataframe(data)
    options_builder.configure_selection(selection_mode='single',use_checkbox=True)
    grid_options = options_builder.build()
    grid = AgGrid(data,gridOptions=grid_options,theme="balham")
    sel_row = grid["selected_rows"]

    if sel_row:
        caption = sel_row[0]['Numero da Nota Fiscal']
        query_romaneio = f"SELECT num_NF, num_volume_eq, codigo, desc_material, quantidade, tipo_embalagem, peso, local FROM packing_list WHERE num_NF ='{caption}' "
        data_PL = pd.read_sql(query_romaneio, connection)
        AgGrid(data_PL)
    connection.close()


# Função para adicionar um novo item
def adicionar_item2():
    select_tipo = st.selectbox("Tipos de Recebimento", ["Lista de Materias", "Equipamentos", "Estrutura Metálica"])
    if(select_tipo == "Lista de Materias"):
        st.subheader("Adicionar Lista de Materias")

        categoria_romaneio = "1"
        num_NF = st.number_input("Numero da NF (Número)", min_value=0)
        item = st.text_input("Nome do item (Texto)")    
        fornecedor = st.selectbox("Fornecedor (Texto)", exibir_itens("Fornecedor", "nome_fornecedor"))
        pedido_compra = st.text_input("Pedido de Compra (Texto)")
        col1, col2 = st.columns(2)
        with col1: 
            manual_input = st.button("Preencher Manualmente")
        with col2: 
            lote_input = st.button("Preencher em Lote")

        if(manual_input):

            desc_item = st.text_area("Descrição do material (Texto)")
            col1, col2, col3 = st.columns(3)
            with col1:
                area = st.text_input("Área (Texto)")
            with col2:
                quantidade = st.number_input("Quantidade (Número)", min_value=0)
            with col3:    
                peso = st.number_input("Peso total (Kg) (Número)", min_value=0)
            local = st.selectbox("Local onde será armazenado", exibir_itens("local", "titulo_local"))
            adicionar = st.button("Adicionar")

            
            if (adicionar):
                connection = conectar_bd()
                cursor = connection.cursor()
                cursor.execute(
                    '''INSERT INTO romaneio (categoria, num_NF, item, fornecedor, pedido_compra, desc_material, area, quantidade, peso, local) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        categoria_romaneio,
                        num_NF,
                        item,
                        fornecedor,
                        pedido_compra,
                        desc_item,
                        area,
                        quantidade,
                        peso,
                        local
                    ),
                )
                connection.commit()
                cursor.close()
                connection.close()
                st.success("Item adicionado com sucesso.")
                
        if(lote_input):
            #Adiciondar aqruivo
            uploaded_file = st.file_uploader("Packing List")
            adicionar = st.button("Adicionar")

            if(adicionar):
                planilha = pd.read_excel(uploaded_file)
                for row in planilha.to_dict(orient="records"):
                    print("AQUIIIIIIIIIIIII!!!!!!!!!!!!!!")
                    print(row)
                    cursor.execute(f"INSERT INTO packing_list (num_volume_eq, codigo, descricao, quantidade, tipo_embalagem, peso, local) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                row['VOLUME'], row['CODIGO'], row['DESCRICAO'], row['QTD'], row['TIPO EMBALAGEM'], row['PESO'], row['LOCAL'])
                    connection.commit()
            


    if(select_tipo == "Equipamentos"):
        st.subheader("Adicionar Equipamentos")
        categoria_romaneio = "2"
        num_NF = st.number_input("Numero da NF (Número)", min_value=0)
        item = st.text_input("Nome/Código do item (Texto)")    
        fornecedor = st.selectbox("Fornecedor (Texto)", exibir_itens("Fornecedor", "nome_fornecedor"))
        pedido_compra = st.text_input("Pedido de Compra (Texto)")

        uploaded_file = st.file_uploader("Packing List")
        #Adiciondar aqruivo
        adicionar = st.button("Adicionar")
        
        if (adicionar):
            connection = conectar_bd()
            cursor = connection.cursor()
            cursor.execute(
                '''INSERT INTO romaneio (categoria, num_NF, item, fornecedor, pedido_compra) VALUES (?, ?, ?, ?, ?)''',
                (
                    categoria_romaneio,
                    num_NF,
                    item,
                    fornecedor,
                    pedido_compra
                ),
            )
            connection.commit()

            st.success("Item adicionado com sucesso.")
            planilha = pd.read_excel(uploaded_file)
            for row in planilha.to_dict(orient="records"):
                print("AQUIIIIIIIIIIIII!!!!!!!!!!!!!!")
                print(row)
                cursor.execute(f"INSERT INTO packing_list (num_NF, num_volume_eq, codigo, desc_material, quantidade, tipo_embalagem, peso, local) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            num_NF, row['VOLUME'], row['CODIGO'], row['DESCRICAO'], row['QTD'], row['TIPO EMBALAGEM'], row['PESO'], row['LOCAL'])
                connection.commit()




    if(select_tipo == "Estrutura Metálica"):
        st.subheader("Adicionar Estrutura Metálica")
        categoria_romaneio = "3"
        num_NF = st.number_input("Numero da NF (Número)", min_value=0)
        item = st.text_input("Nome do item (Texto)")    
        fornecedor = st.selectbox("Fornecedor (Texto)", exibir_itens("Fornecedor", "nome_fornecedor"))
        pedido_compra = st.text_input("Pedido de Compra (Texto)")
        col1, col2 = st.columns(2)
        with col1: 
            manual_input = st.button("Preencher Manualmente")
        with col2: 
            lote_input = st.button("Preencher em Lote")

        if(manual_input):
            num_desenho = st.number_input("Numero do Desenho (Número)", min_value=0)
            desc_es = st.text_area("Descrição (Texto)")

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                area = st.text_input("Área (Texto)")
            with col2:
                quantidade = st.number_input("Quantidade (Número)", min_value=0)
            with col3:    
                peso = st.number_input("Peso total (Kg) (Número)", min_value=0)
            with col4:    
                num_volume_eq = st.number_input("Número do volume (Número)", min_value=0)
            with col5:    
                tag = st.text_input("TAG (Texto)")  
            local = st.selectbox("Local onde será armazenado", exibir_itens("local", "titulo_local"))
           
            if st.button("Adicionar"):
                connection = conectar_bd()
                cursor = connection.cursor()
                cursor.execute(
                    '''INSERT INTO romaneio (categoria, num_NF, item, fornecedor, pedido_compra, desc_es, num_desenho, tag,  area, quantidade, peso, local) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        categoria_romaneio,
                        num_NF,
                        item,
                        fornecedor,
                        pedido_compra,
                        desc_es,
                        num_desenho,
                        tag,
                        area,
                        quantidade,
                        peso,
                        local
                    ),
                )
                connection.commit()
                cursor.close()
                connection.close()
                st.success("Item adicionado com sucesso.")

        if(lote_input):
            connection = conectar_bd()
            cursor = connection.cursor()
            planilha = pd.read_excel(uploaded_file)
            for row in planilha.to_dict(orient="records"):
                print("AQUIIIIIIIIIIIII!!!!!!!!!!!!!!")
                print(row)
                cursor.execute(f"INSERT INTO packing_list (num_volume_eq, codigo, descricao, quantidade, tipo_embalagem, peso, local) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            row['VOLUME'], row['CODIGO'], row['DESCRICAO'], row['QTD'], row['TIPO EMBALAGEM'], row['PESO'], row['LOCAL'])
                connection.commit()

# Função para atualizar um item existente
def atualizar_item2():
    st.subheader("Atualizar Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, produto FROM romaneio")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Atualizado", item_ids)
    produto = st.text_input("Novo nome do Produto")
    quantidade = st.number_input("Nova Quantidade", min_value=0)
    if st.button("Atualizar"):
        item_id = item_id.split(":")[0]
        cursor.execute(
            "UPDATE romaneio SET produto = ?, quantidade = ? WHERE id = ?",
            (produto, quantidade, item_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item atualizado com sucesso.")


# Função para remover um item
def remover_item2():
    st.subheader("Remover Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, produto FROM romaneio")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Removido", item_ids)
    if st.button("Remover"):
        item_id = item_id.split(":")[0]
        cursor.execute("DELETE FROM romaneio WHERE id = ?", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item removido com sucesso.")


# ________________Conexão Local BD____________________________


# Função para exibir os dados
def exibir_dados3():
    connection = conectar_bd()
    query = "SELECT titulo_local, status, convert(VARCHAR, data_utilizacao, 103) as 'data_utilizacao', espaco_faltante FROM Local"
    data = pd.read_sql(query, connection).rename(columns=RENAME["Local"])
    st.subheader("Dados do Estoque")
    st.table(data)
    connection.close()


# Função para adicionar um novo item
def adicionar_item3():
    st.subheader("Adicionar Item")
    titulo_local = st.text_input("Nome do Local")
    status = st.text_input("Status")
    data_utilizacao = st.date_input("Data da última alocação")
    espaco_faltante = st.number_input("Espaço faltante (em %)")
    print("Não converteu: ", data_utilizacao)
    print("Tipo: ", type(data_utilizacao))
    # data_utilizacao  = datetime.strptime(data_utilizacao, '%d/%m/%Y')
    # st.write("Converteu: " + data_utilizacao)
    if st.button("Adicionar"):
        connection = conectar_bd()
        cursor = connection.cursor()
        cursor.execute(
            '''INSERT INTO Local (titulo_local, status, data_utilizacao, espaco_faltante) VALUES (?, ?, ?, ?)''',
            (titulo_local, status, data_utilizacao, espaco_faltante),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item adicionado com sucesso.")

# Função para atualizar um item existente
def atualizar_item3():
    st.subheader("Atualizar Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, titulo_local FROM Local")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Atualizado", item_ids)
    nome_local = st.text_input("Novo nome do Local")
    data_att = st.date_input("Data à atualizar")
    if st.button("Atualizar"):
        item_id = item_id.split(":")[0]
        cursor.execute(
            "UPDATE Local SET titulo_local = ?, data_utilizacao = ? WHERE id = ?",
            (nome_local, data_att, item_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item atualizado com sucesso.")


# Função para remover um item
def remover_item3():
    st.subheader("Remover Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, titulo_local FROM Local")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Removido", item_ids)
    if st.button("Remover"):
        item_id = item_id.split(":")[0]
        cursor.execute("DELETE FROM Local WHERE id = ?", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item removido com sucesso.")


# ________________Conexão Fornecedor BD____________________________


# Função para exibir os dados
def exibir_dados4():
    connection = conectar_bd()
    query = "SELECT nome_fornecedor, num_fornecedor FROM Fornecedor"
    data = pd.read_sql(query, connection).rename(columns=RENAME["Fornecedor"])
    st.subheader("Dados do Estoque")
    st.table(data)
    connection.close()


# Função para adicionar um novo item
def adicionar_item4():
    st.subheader("Adicionar Item")
    nome_fornecedor = st.text_input("Nome do Fornecedor")
    num_fornecedor = st.number_input("Numero do Fornecedor")

    if st.button("Adicionar"):
        connection = conectar_bd()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Fornecedor (nome_fornecedor, num_fornecedor) VALUES (?, ?)",
            (nome_fornecedor, num_fornecedor),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item adicionado com sucesso.")

# Função para atualizar um item existente
def atualizar_item4():
    st.subheader("Atualizar Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome_fornecedor FROM Fornecedor")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Atualizado", item_ids)
    nome_forne = st.text_input("Novo nome do Fornecedor")
    num_forne = st.number_input("Novo numero do Fornecedor")
    if st.button("Atualizar"):
        item_id = item_id.split(":")[0]
        cursor.execute(
            "UPDATE Fornecedor SET nome_fornecedor = ?, num_fornecedor = ? WHERE id = ?",
            (nome_forne, num_forne, item_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item atualizado com sucesso.")

# Função para remover um item
def remover_item4():
    st.subheader("Remover Item")
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome_fornecedor FROM Fornecedor")
    items = cursor.fetchall()
    item_ids = [str(item[0]) + ": " + item[1] for item in items]
    item_id = st.selectbox("Selecione o Item a ser Removido", item_ids)
    if st.button("Remover"):
        item_id = item_id.split(":")[0]
        cursor.execute("DELETE FROM Fornecedor WHERE id = ?", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Item removido com sucesso.")

# ________________Funções auxiliares____________________________

def localizarArmazens():
    st.subheader("Localizar Armazens")
    chart_data = pd.DataFrame(
        np.random.randn(20, 2) / [50, 50] + [-19.87, -43.39], columns=["lat", "lon"]
    )
    # st.text(chart_data)
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=-19.87, 
                longitude=-43.39, 
                # latitude=37.76,
                # longitude=-122.4,
                zoom=11,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=chart_data,
                    get_position="[lon, lat]",
                    radius=200,
                    elevation_scale=4,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    data=chart_data,
                    get_position="[lon, lat]",
                    get_color="[200, 30, 0, 160]",
                    get_radius=200,
                ),
            ],
        )
    )

def exibir_all():
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tabelas = cursor.fetchall()

    dados_juntados = []
    for tabela in tabelas:
        tabela = tabela[0]  # Nome da tabela
        cursor.execute(f"SELECT * FROM {tabela}")
        dados_tabela = cursor.fetchall()
        dados_juntados.extend(dados_tabela)
    AgGrid(dados_juntados)
    cursor.close()
    connection.close()
    

def exibir_itens(tabela, coluna):
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute(f"SELECT id, {coluna} FROM {tabela}")
    items = cursor.fetchall()
    item_ids = [item[1] for item in items]    
    
    return item_ids

def importar_imagem(url):
    try:
        # Baixar a imagem a partir da URL
        with urllib.request.urlopen(url) as resposta:
            imagem_bytes = resposta.read()

        # Abrir a imagem usando o Pillow
        imagem = Image.open(BytesIO(imagem_bytes))

        # Exibir a imagem
        imagem.show()
        st.sidebar.image(imagem)

    except Exception as e:
        print("Ocorreu um erro:", e)

# ________________VOID MAIN____________________________
# fazendo o login
names = ["Lucas Angelo", "Frederico Oliveira"]
usernames = ["langelo", "foliveira"]

credentials = {"usernames":{}}
#cripto grafando a senha
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)
#compactando as senhas na credentials
for un, name, pw in zip(usernames, names, hashed_passwords):
    user_dict = {"name":name,"password":pw}
    credentials["usernames"].update({un:user_dict})

authenticator = stauth.Authenticate(credentials, "sales_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Usuário ou senha incorretos")

if authentication_status == None:
    st.warning("Por favor, insera o cadastro")

if authentication_status:

    # Configurações da página
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title("Sistema de Gestão de Estoque do Almoxarifado")
    # importar_imagem("https://arcadiso365.sharepoint.com/sites/intranet/SiteAssets/Debble/logo.png")

    # st.sidebar.image(img)
    st.sidebar.title(f"Bem vindo {name}")

    # Criar tabela caso não exista
    criar_tabelaAll("estoque", "CREATE TABLE estoque (id int IDENTITY(1,1) PRIMARY KEY,produto VARCHAR(255),quantidade int)")
    criar_tabelaAll("romaneio", "CREATE TABLE romaneio (id int IDENTITY(1,1) PRIMARY KEY,categoria INT NOT NULL CHECK (categoria IN (1, 2, 3)),num_NF INT,item VARCHAR(255),fornecedor VARCHAR(255),pedido_compra VARCHAR(255),num_desenho INT,desc_material TEXT,desc_es TEXT,area VARCHAR(255),TAG VARCHAR(255),quantidade INT,peso INT,local VARCHAR(255))")
    criar_tabelaAll("Local", "CREATE TABLE Local (id int IDENTITY(1,1) PRIMARY KEY,titulo_local VARCHAR(255),status VARCHAR(255),data_utilizacao DATE,espaco_faltante INT)")
    criar_tabelaAll("Fornecedor", "CREATE TABLE Fornecedor (id int IDENTITY(1,1) PRIMARY KEY,nome_fornecedor VARCHAR(255),num_fornecedor INT)")
    criar_tabelaAll("Colaborador", "CREATE TABLE Colaborador (id int IDENTITY(1,1) PRIMARY KEY,nome_colaborador VARCHAR(255),num_colaborador INT)")
    criar_tabelaAll("packing_list", "CREATE TABLE packing_list (id int IDENTITY(1,1) PRIMARY KEY,num_NF INT, num_volume_eq INT,codigo VARCHAR(255),desc_material TEXT,quantidade INT,tipo_embalagem VARCHAR(255),peso INT,local VARCHAR(255))")
 
    # Barra de navegação
    menu = ["Exibir Dados", "Adicionar Item", "Atualizar Item", "Remover Item"]
    operation = ["Exibir Dados", "Adicionar Item"]

    paginaSelecionada = st.sidebar.selectbox(
        "Selecione o Módulo", ["Saída de Materias", "Entrada de Materias", "Cadastro de Local", "Cadastro de Fornecedor", "Dashboards"]
    )
    def carregar_dados(read, create, update, delete):
        selected= option_menu(
            menu_title = None,
            options = ["Read", "Create", "Update", "Delete"],
            icons = ["book", "pencil-square", "arrow-clockwise", "trash"],
            menu_icon = "cast",
            default_index = 0,
            orientation = "horizontal",
        )

        if selected== "Read":
            read()

        if selected== "Create":
            create()

        if selected== "Update":
            update()

        if selected== "Delete":
            delete()


    if paginaSelecionada == "Saída de Materias":
        carregar_dados(exibir_dados, adicionar_item, atualizar_item, remover_item)

    elif paginaSelecionada == "Entrada de Materias":
        carregar_dados(exibir_dados2, adicionar_item2, atualizar_item2, remover_item2)

    elif paginaSelecionada == "Cadastro de Local":
        carregar_dados(exibir_dados3, adicionar_item3, atualizar_item3, remover_item3)

    elif paginaSelecionada == "Cadastro de Fornecedor":
        carregar_dados(exibir_dados4, adicionar_item4, atualizar_item4, remover_item4)

    elif paginaSelecionada == "Dashboards":
        exibir_all()