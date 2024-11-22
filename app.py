import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import openpyxl
import io
import os

# Configuração da página
st.set_page_config(
    page_title="Extrator de Imagem para Excel",
    page_icon="📊",
    layout="wide"
)

# Configuração inicial do Streamlit
if 'dados_extraidos' not in st.session_state:
    st.session_state.dados_extraidos = None

def processar_imagem(imagem):
    """
    Extrai texto da imagem e estrutura os dados
    """
    try:
        # Converte imagem para texto
        texto = pytesseract.image_to_string(Image.open(imagem), lang='por')
        
        # Lista para armazenar os itens processados
        itens = []
        
        # Processa cada linha
        for linha in texto.split('\n'):
            if not linha.strip():  # Ignora linhas vazias
                continue
            
            try:
                # Separa quantidade do resto
                partes = linha.split('.')
                if len(partes) < 2:
                    continue
                    
                quantidade = partes[0].strip()
                # Remove caracteres não numéricos da quantidade
                quantidade = ''.join(c for c in quantidade if c.isdigit())
                
                # Resto da linha é o item com especificações
                descricao = '.'.join(partes[1:]).strip()
                
                # Adiciona à lista de itens
                itens.append({
                    'Quantidade': quantidade,
                    'Descrição': descricao
                })
                
            except Exception as e:
                st.warning(f"Erro ao processar linha: {linha}")
                continue
        
        return pd.DataFrame(itens)
    
    except Exception as e:
        st.error(f"Erro ao processar imagem: {str(e)}")
        return None

def criar_excel(df):
    """
    Cria arquivo Excel com os dados processados
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)
    return output

def main():
    # Título e descrição
    st.title("📊 Extrator de Lista para Excel")
    
    # CSS para remover elementos da interface do Streamlit
    st.markdown("""
        <style>
        /* Esconde os ícones do topo direito */
        section[data-testid="stSidebar"] > div {
            display: none;
        }

        /* Esconde o menu superior direito completo */
        .menu {
            display: none !important;
        }

        /* Esconde os botões de ação no topo */
        .stActionButton, .stDeployButton {
            display: none !important;
        }

        /* Esconde o Manage app no rodapé */
        footer {
            display: none !important;
        }

        /* Remove a barra de ferramentas superior */
        .stToolbar {
            display: none !important;
        }

        /* Esconde elementos específicos do header */
        [data-testid="stHeader"] {
            display: none !important;
        }

        /* Reduz o espaço superior */
        .block-container {
            padding-top: 2rem !important;
        }

        /* Esconde elementos do Streamlit */
        .viewerBadge_container__1QSob {
            display: none !important;
        }
        
        .st-emotion-cache-1rs6os {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Área de upload
    st.header("1. Selecione a imagem da lista")
    imagem = st.file_uploader(
        "Escolha uma imagem",
        type=['png', 'jpg', 'jpeg'],
        help="Formatos suportados: PNG, JPG"
    )
    
    if imagem:
        # Mostra a imagem
        st.image(imagem, caption="Imagem carregada", use_column_width=True)
        
        # Botão para processar
        if st.button("Processar Imagem"):
            with st.spinner('Processando imagem...'):
                # Processa a imagem
                df = processar_imagem(imagem)
                
                if df is not None and not df.empty:
                    st.session_state.dados_extraidos = df
                    st.success('✅ Processamento concluído!')
                else:
                    st.error('❌ Erro ao processar imagem. Tente novamente.')
        
        # Mostra resultados se houver dados processados
        if st.session_state.dados_extraidos is not None:
            st.header("2. Resultados Extraídos")
            
            # Mostra tabela editável
            df_editado = st.data_editor(
                st.session_state.dados_extraidos,
                num_rows="dynamic",
                use_container_width=True
            )
            
            # Botão para baixar Excel
            excel_buffer = criar_excel(df_editado)
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_buffer,
                file_name="lista_extraida.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Instruções de uso
    with st.expander("ℹ️ Como usar", expanded=False):
        st.markdown("""
            **Como usar o sistema:**
            1. Clique em 'Browse files' ou arraste uma imagem
            2. Aguarde o upload da imagem
            3. Clique em 'Processar Imagem'
            4. Verifique e edite os dados se necessário
            5. Clique em 'Baixar Excel' para salvar
            
            **Observações:**
            - A imagem deve estar legível
            - Formatos suportados: PNG, JPG
            - Você pode editar os dados antes de baixar
            """)

if __name__ == "__main__":
    main()
```
