import streamlit as st
import pandas as pd
import io
import base64
from openai import OpenAI
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Extrator de Imagem para Excel",
    page_icon="📊",
    layout="wide"
)

# Configuração do OpenAI
def init_openai():
    """
    Inicializa o cliente OpenAI com a chave da API
    """
    try:
        if 'OPENAI_API_KEY' not in st.secrets:
            st.error('Chave da API OpenAI não encontrada nos secrets!')
            st.stop()
            
        return OpenAI(
            api_key=st.secrets['OPENAI_API_KEY']
        )
    except Exception as e:
        st.error(f"Erro ao inicializar OpenAI: {str(e)}")
        st.stop()
        
def processar_imagem_com_openai(client, imagem):
    """
    Usa a API da OpenAI para extrair texto da imagem
    """
    try:
        # Converte a imagem para base64
        image = Image.open(imagem)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Esta é uma lista de itens com quantidades. Por favor, extraia para cada linha: a quantidade e a descrição do item. Retorne em formato estruturado."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{img_str}"
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        # Processa a resposta da API
        texto_extraido = response.choices[0].message.content
        return estruturar_dados(texto_extraido)

    except Exception as e:
        st.error(f"Erro ao processar imagem: {str(e)}")
        return None

def estruturar_dados(texto):
    """
    Converte o texto extraído em DataFrame
    """
    linhas = texto.strip().split('\n')
    itens = []
    
    for linha in linhas:
        if not linha.strip():
            continue
        
        try:
            # Assume que a quantidade está no início da linha
            partes = linha.split('.')
            if len(partes) >= 2:
                quantidade = partes[0].strip()
                descricao = '.'.join(partes[1:]).strip()
                
                itens.append({
                    'Quantidade': quantidade,
                    'Descrição': descricao
                })
        except Exception as e:
            st.warning(f"Erro ao processar linha: {linha}")
            continue
    
    return pd.DataFrame(itens)

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
        /* Esconde os elementos da interface */
        section[data-testid="stSidebar"] > div {
            display: none;
        }
        .menu, .stActionButton, .stDeployButton, footer, .stToolbar {
            display: none !important;
        }
        [data-testid="stHeader"] {
            display: none !important;
        }
        .block-container {
            padding-top: 2rem !important;
        }
        .viewerBadge_container__1QSob, .st-emotion-cache-1rs6os {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

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
        
        # Inicializa cliente OpenAI
        client = init_openai()
        
        # Botão para processar
        if st.button("Processar Imagem"):
            with st.spinner('Processando imagem...'):
                # Processa a imagem
                df = processar_imagem_com_openai(client, imagem)
                
                if df is not None and not df.empty:
                    st.session_state.dados_extraidos = df
                    st.success('✅ Processamento concluído!')
                else:
                    st.error('❌ Erro ao processar imagem. Tente novamente.')
        
        # Mostra resultados se houver dados processados
        if hasattr(st.session_state, 'dados_extraidos') and st.session_state.dados_extraidos is not None:
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

if __name__ == "__main__":
    main()
