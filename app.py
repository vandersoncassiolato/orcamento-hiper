import streamlit as st
import pandas as pd
from anthropic import Anthropic
import io
import base64
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Extrator de Imagem para Excel",
    page_icon="📊",
    layout="wide"
)

def init_claude():
    try:
        st.write("Debug - Secrets disponíveis:", st.secrets)  # Debug completo
        
        if 'CLAUDE_API_KEY' not in st.secrets:
            st.error('Chave da API Claude não encontrada nos secrets!')
            st.write("Secrets esperados: CLAUDE_API_KEY")
            st.write("Secrets encontrados:", st.secrets)
            st.stop()
            
        return Anthropic(api_key=str(st.secrets['CLAUDE_API_KEY']))
    except Exception as e:
        st.error(f"Erro ao inicializar Claude: {str(e)}")
        st.write("Erro completo:", str(e))
        st.stop()

def processar_imagem_com_claude(client, imagem):
    """
    Usa a API do Claude para extrair texto da imagem
    """
    try:
        # Converte a imagem para base64
        buffered = io.BytesIO()
        Image.open(imagem).save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Nesta imagem há uma lista de itens com quantidades. Por favor extraia as quantidades e descrições no formato: quantidade e item. Retorne apenas os dados extraídos, sem comentários adicionais."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_str
                        }
                    }
                ]
            }]
        )

        texto_extraido = message.content[0].text
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
    st.title("📊 Extrator de Lista para Excel")
    
    # CSS para interface limpa
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] > div {display: none;}
        .menu {display: none !important;}
        .stActionButton, .stDeployButton, footer, .stToolbar {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        .block-container {padding-top: 2rem !important;}
        .viewerBadge_container__1QSob, .st-emotion-cache-1rs6os {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

    # Instruções
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

    # Upload
    st.header("1. Selecione a imagem da lista")
    imagem = st.file_uploader(
        "Escolha uma imagem",
        type=['png', 'jpg', 'jpeg'],
        help="Formatos suportados: PNG, JPG"
    )
    
    if imagem:
        st.image(imagem, caption="Imagem carregada", use_column_width=True)
        
        client = init_claude()
        
        if st.button("Processar Imagem"):
            with st.spinner('Processando imagem...'):
                df = processar_imagem_com_claude(client, imagem)
                
                if df is not None and not df.empty:
                    st.session_state.dados_extraidos = df
                    st.success('✅ Processamento concluído!')
                else:
                    st.error('❌ Erro ao processar imagem. Tente novamente.')
        
        if hasattr(st.session_state, 'dados_extraidos') and st.session_state.dados_extraidos is not None:
            st.header("2. Resultados Extraídos")
            
            df_editado = st.data_editor(
                st.session_state.dados_extraidos,
                num_rows="dynamic",
                use_container_width=True
            )
            
            excel_buffer = criar_excel(df_editado)
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_buffer,
                file_name="lista_extraida.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
