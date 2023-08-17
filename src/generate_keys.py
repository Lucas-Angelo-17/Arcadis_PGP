import pickle
from pathlib import Path
import streamlit_authenticator as stauth

names = ["Lucas Angelo", "Fred Oliveira"]
usernames = ["langelo", "foliveira"]
passwords = ["abc123", "def456"]

# Usando o módulo 'Hasher' do 'stauth' para criar senhas criptografadas
# A função 'generate()' cria senhas criptografadas a partir das senhas fornecidas
hashed_passwords = stauth.Hasher(passwords).generate()

# Criando o caminho completo para o arquivo onde as senhas criptografadas serão armazenadas
file_path = Path(__file__).parent / "hashed_pw.pkl"

# Abrindo o arquivo no modo de escrita binária para salvar as senhas criptografadas
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)