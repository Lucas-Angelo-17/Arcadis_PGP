from db_conection import conectar_bd

def create_single_tabel():
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute(
        """
        IF NOT EXISTS(SELECT * FROM sys.tables WHERE name = 'produtos')
        BEGIN
            CREATE TABLE produtos (
                id int IDENTITY(1,1) PRIMARY KEY,
                codigo int,
                nome VARCHAR(20),
                quantidade int,
            )
        END
        """
    )
    connection.commit()
    cursor.close()
    connection.close()

def create_generic_table(tabela, createTable):
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

