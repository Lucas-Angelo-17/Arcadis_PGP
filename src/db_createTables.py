from db_conection import conectar_bd

def create_single_tabel():
    connection = conectar_bd()
    cursor = connection.cursor()
    cursor.execute(
        """
        IF NOT EXISTS(SELECT * FROM sys.tables WHERE name = 'estoque')
        BEGIN
            CREATE TABLE estoque (
                id int IDENTITY(1,1) PRIMARY KEY,
                produto VARCHAR(20),
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

