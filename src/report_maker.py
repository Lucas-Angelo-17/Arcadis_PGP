import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3
import io

def create_report(nome_colab, data_req, db_data, id_requisisao, new_quant):
    # Criar o relatório usando o ReportLab
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    title = f"Requisição Número {id_requisisao}"
    text = f"Esta requisição foi realizada pelo colaborador: {nome_colab}, na data: {data_req}, requisitando materiais tabelados abaixos."

    # Criação do título e texto usando o ReportLab
    title_paragraph = Paragraph(title, styles['Title'])
    text_paragraph = Paragraph(text, styles['Normal'])

    cabecalho = [
        ["PC", "Código", "NF", "Descrição", "Uni. Med.", "Local", "QNT. Requisitada"] # TAG
    ]
    # Função para juntar a quantidade requisitada com a lista de dados
    def merge_lists(list_of_arrays, list_of_integers):
        if len(list_of_arrays) != len(list_of_integers):
            raise ValueError("Both lists should have the same number of elements.")
        output = []
        for i in range(len(list_of_arrays)):
            array = list_of_arrays[i]
            integer = list_of_integers[i]
            array.append(integer)
            output.append(array)
        return output

    table = Table(cabecalho + merge_lists(db_data.values.tolist(), new_quant))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Adicionar o texto após a tabela
    after_table_text1 = "Entregue por:"
    after_table_text2 = "Recebido por:"
    after_table_paragraph1 = Paragraph(after_table_text1, styles['Normal'])
    after_table_paragraph2 = Paragraph(after_table_text2, styles['Normal'])

    # Criar uma tabela com duas colunas para os textos e linhas abaixo de cada texto
    text_table = Table([[after_table_paragraph1, after_table_paragraph2]])
    text_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    def draw_lines(canvas, doc):
        # Desenhar as linhas abaixo de cada texto
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)

        text_table_x, text_table_y = text_table.wrap(doc.width, doc.bottomMargin)
        text_table.drawOn(canvas, doc.leftMargin, doc.bottomMargin - text_table_y)

        canvas.line(doc.leftMargin, doc.bottomMargin - 15, doc.leftMargin + doc.width / 2 - 20, doc.bottomMargin - 15)
        canvas.line(doc.leftMargin + doc.width / 2, doc.bottomMargin - 15, doc.leftMargin + doc.width, doc.bottomMargin - 15)

    # Adicionando os elementos ao PDF
    elements = [title_paragraph, text_paragraph, table]
    doc.build(elements, onFirstPage=draw_lines)

    # Reinicie o ponteiro do buffer para o início
    buffer.seek(0)
    st.download_button("Download Requisição", data=buffer, file_name="relatorio.pdf")