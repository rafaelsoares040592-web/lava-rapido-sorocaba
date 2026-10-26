import pandas as pd
import streamlit as st
from datetime import date
from supabase import create_client, Client
import requests
import json

# ==========================================
# CONFIGURAÇÃO DE SEGURANÇA (SECRETS)
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Chave da API do Gemini via secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Configuração da Página Web
st.set_page_config(page_title="LavaRápido Inteligente", layout="wide", page_icon="🚗")
st.title("🚗 LavaRápido Inteligente — Sistema de Gestão Profissional")
st.write("Controle completo de caixa, fila do pátio, agendamentos e assistente inteligente com Google Gemini.")

# Criando as Abas de Navegação do MVP
aba1, aba2, aba3, aba4 = st.tabs([
    "💰 Caixa & Faturamento", 
    "📅 Agenda de Veículos", 
    "🅿️ Fila do Pátio & OS", 
    "🤖 Assistente de IA (Gemini)"
])

# ==========================================
# ABA 1: CAIXA E FATURAMENTO
# ==========================================
with aba1:
    st.header("Fluxo de Caixa Operacional")
    
    try:
        response = supabase.table("service_orders").select("*").execute()
        dados_os = response.data
        df_os = pd.DataFrame(dados_os) if dados_os else pd.DataFrame(columns=['id', 'client_name', 'vehicle_model', 'service_name', 'total_amount', 'payment_method', 'status', 'entry_time'])
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        df_os = pd.DataFrame(columns=['id', 'client_name', 'vehicle_model', 'service_name', 'total_amount', 'payment_method', 'status', 'entry_time'])

    faturamento_total = df_os['total_amount'].sum() if not df_os.empty and 'total_amount' in df_os else 0.0
    total_veiculos = len(df_os)

    col1, col2 = st.columns(2)
    col1.metric("Faturamento Total Registrado", f"R$ {faturamento_total:,.2f}")
    col2.metric("Total de Atendimentos", total_veiculos)

    st.subheader("📋 Histórico Geral de Ordens de Serviço")
    if not df_os.empty:
        st.dataframe(df_os, use_container_width=True)
    else:
        st.info("Nenhum atendimento registado na nuvem ainda.")


# ==========================================
# ABA 2: AGENDA DE VEÍCULOS
# ==========================================
with aba2:
    st.header("Agenda Inteligente de Horários")
    st.write("Organize os horários de atendimento para evitar filas e otimizar os boxes.")

    with st.form("form_novo_agendamento"):
        st.subheader("➕ Novo Agendamento / Cliente")
        cli_nome = st.text_input("Nome do Cliente")
        cli_tel = st.text_input("Telefone do Cliente (WhatsApp)")
        vei_modelo = st.text_input("Modelo do Veículo (ex: VW Gol, Jeep Compass)")
        servico_escolhido = st.selectbox("Serviço Desejado", ["Ducha Simples", "Lavagem Completa", "Higienização de Bancos", "Polimento Técnico"])
        
        if servico_escolhido == "Ducha Simples": preco_base = 40.00
        elif servico_escolhido == "Lavagem Completa": preco_base = 70.00
        elif servico_escolhido == "Higienização de Bancos": preco_base = 150.00
        else: preco_base = 200.00
            
        st.write(f"**Valor Estimado:** R$ {preco_base:.2f}")
        
        salvar_agendamento = st.form_submit_button("Confirmar e Enviar para o Pátio")
        if salvar_agendamento and cli_nome and vei_modelo:
            try:
                novo_registro = {
                    "client_name": cli_nome,
                    "vehicle_model": vei_modelo,
                    "service_name": servico_escolhido,
                    "total_amount": preco_base,
                    "payment_method": "Pix",
                    "status": "Aguardando"
                }
                supabase.table("service_orders").insert(novo_registro).execute()
                st.success("Veículo registado e enviado para a fila do pátio com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar agendamento no Supabase: {e}")


# ==========================================
# ABA 3: FILA DO PÁTIO & ORDEM DE SERVIÇO
# ==========================================
with aba3:
    st.header("🅿️ Fila do Pátio em Tempo Real")
    st.write("Acompanhe o status dos veículos que estão no estabelecimento.")

    try:
        response_patio = supabase.table("service_orders").select("*").eq("status", "Aguardando").execute()
        fila_aguardando = response_patio.data
        df_fila = pd.DataFrame(fila_aguardando) if fila_aguardando else pd.DataFrame()
    except:
        df_fila = pd.DataFrame()

    if not df_fila.empty:
        st.dataframe(df_fila, use_container_width=True)
    else:
        st.info("Nenhum veículo aguardando no pátio neste momento.")


# ==========================================
# ABA 4: ASSISTENTE DE IA (GOOGLE GEMINI - REST API)
# ==========================================
with aba4:
    st.header("🤖 Assistente Inteligente (Google Gemini)")
    st.write("Faça perguntas diretas sobre o seu negócio ou crie mensagens profissionais para os clientes.")

    pergunta_dono = st.text_input("O que deseja perguntar à IA sobre o seu lava-rápido?", "Qual é o resumo do nosso faturamento atual e dicas para atrair mais clientes?")

    if st.button("Consultar Inteligência Artificial"):
        if not GEMINI_API_KEY:
            st.error("A chave GEMINI_API_KEY não foi configurada nos secrets do Streamlit.")
        else:
            with st.spinner("A analisar os dados e a estruturar a resposta..."):
                try:
                    prompt_sistema = (
                        f"Você é um consultor de negócios especialista em lava-rápidos no Brasil. "
                        f"Responda de forma prática, comercial e amigável à seguinte questão do dono: '{pergunta_dono}'."
                    )

                    # Utilizando o modelo gemini-2.0-flash ativo e estável via REST API
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{
                            "parts": [{"text": prompt_sistema}]
                        }]
                    }

                    resposta_api = requests.post(url, headers=headers, data=json.dumps(payload))
                    
                    if resposta_api.status_code == 200:
                        dados_resposta = resposta_api.json()
                        texto_gerado = dados_resposta["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("Análise gerada com sucesso!")
                        st.markdown(texto_gerado)
                    else:
                        st.error(f"Erro na API do Gemini (Código {resposta_api.status_code}): {resposta_api.text}")

                except Exception as e:
                    st.error(f"Erro de conexão com o serviço de IA: {e}")
