import pandas as pd
import streamlit as st
from datetime import date
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÃO DO SUPABASE (SECRETS NA NUVEM)
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da Página Web
st.set_page_config(page_title="Lava Rápido Sorocaba Clean", layout="wide")
st.title("🚗 Sistema de Gestão - Lava Rápido Sorocaba Clean (Nuvem / Supabase)")
st.write("Controle completo de caixa, agenda de veículos e mensagens inteligentes integrado à nuvem com segurança máxima.")

# Criando as Abas de Navegação no Navegador
aba1, aba2, aba3 = st.tabs(["💰 Caixa & Atendimentos", "📅 Agenda de Veículos", "🤖 Assistente de IA para Clientes"])

# ==========================================
# ABA 1: CAIXA E ATENDIMENTOS
# ==========================================
with aba1:
    st.header("Fluxo de Caixa Operacional")
    
    # Buscando dados do Supabase para o Caixa
    try:
        response = supabase.table("atendimento_lavarapido").select("*").execute()
        dados_atendimento = response.data
        df_lavagens = pd.DataFrame(dados_atendimento) if dados_atendimento else pd.DataFrame(columns=['id_atendimento', 'nome_cliente', 'modelo_veiculo', 'tipo_servico', 'valor_servico', 'forma_pagamento', 'data_atendimento'])
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        df_lavagens = pd.DataFrame(columns=['id_atendimento', 'nome_cliente', 'modelo_veiculo', 'tipo_servico', 'valor_servico', 'forma_pagamento', 'data_atendimento'])

    faturamento_hoje = df_lavagens['valor_servico'].sum() if not df_lavagens.empty and 'valor_servico' in df_lavagens else 0.0
    total_carros = len(df_lavagens)

    col1, col2 = st.columns(2)
    col1.metric("Faturamento Total Registrado", f"R$ {faturamento_hoje:,.2f}")
    col2.metric("Total de Veículos Atendidos", total_carros)

    st.subheader("📋 Histórico de Veículos Atendidos")
    if not df_lavagens.empty:
        st.dataframe(df_lavagens, width='stretch')
    else:
        st.info("Nenhum atendimento registrado na nuvem ainda.")

    st.subheader("➕ Registrar Nova Lavagem Concluída")
    with st.form("form_lavagem"):
        novo_id = len(df_lavagens) + 1
        cliente = st.text_input("Nome do Cliente")
        veiculo = st.text_input("Modelo do Veículo (ex: Toyota Corolla)")
        servico = st.selectbox("Tipo de Serviço", ["Ducha Simples", "Lavagem Completa", "Higienização de Bancos", "Polimento"])
        
        if servico == "Ducha Simples": valor = 40.00
        elif servico == "Lavagem Completa": valor = 70.00
        elif servico == "Higienização de Bancos": valor = 150.00
        else: valor = 200.00
            
        st.write(f"**Valor Sugerido:** R$ {valor:.2f}")
        pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
        
        salvar = st.form_submit_button("Concluir e Registrar no Caixa")
        if salvar and cliente and veiculo:
            try:
                novo_registro = {
                    "id_atendimento": novo_id,
                    "nome_cliente": cliente,
                    "modelo_veiculo": veiculo,
                    "tipo_servico": servico,
                    "valor_servico": valor,
                    "forma_pagamento": pagamento,
                    "data_atendimento": str(date.today())
                }
                supabase.table("atendimento_lavarapido").insert(novo_registro).execute()
                st.success("Lavagem registrada com sucesso na nuvem!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar no Supabase: {e}")

# ==========================================
# ABA 2: AGENDA DE CARROS
# ==========================================
with aba2:
    st.header("Agenda de Veículos para Lavagem")
    st.write("Organize os horários dos clientes para evitar filas no pátio.")

    # Buscando dados de agendamento do Supabase
    try:
        response_agenda = supabase.table("agenda_lavarapido").select("*").execute()
        dados_agenda = response_agenda.data
        df_agenda = pd.DataFrame(dados_agenda) if dados_agenda else pd.DataFrame(columns=['id_agendamento', 'nome_cliente', 'modelo_veiculo', 'horario_pretendido', 'status_agenda'])
    except Exception as e:
        st.error(f"Erro ao carregar agenda do Supabase: {e}")
        df_agenda = pd.DataFrame(columns=['id_agendamento', 'nome_cliente', 'modelo_veiculo', 'horario_pretendido', 'status_agenda'])

    st.subheader("📅 Próximos Horários Agendados")
    if not df_agenda.empty:
        st.dataframe(df_agenda, width='stretch')
    else:
        st.info("Nenhum carro agendado no momento.")

    st.subheader("➕ Agendar Novo Veículo")
    with st.form("form_agenda"):
        id_ag = len(df_agenda) + 1
        cli_agenda = st.text_input("Nome do Cliente (Agenda)")
        vei_agenda = st.text_input("Modelo do Veículo (Agenda)")
        horario = st.selectbox("Horário Pretendido", ["08:30", "10:00", "11:30", "13:30", "15:00", "16:30"])
        
        agendar = st.form_submit_button("Confirmar Agendamento")
        if agendar and cli_agenda and vei_agenda:
            try:
                novo_agendamento = {
                    "id_agendamento": id_ag,
                    "nome_cliente": cli_agenda,
                    "modelo_veiculo": vei_agenda,
                    "horario_pretendido": horario,
                    "status_agenda": "Agendado"
                }
                supabase.table("agenda_lavarapido").insert(novo_agendamento).execute()
                st.success(f"Carro de {cli_agenda} agendado para as {horario} com sucesso na nuvem!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar agendamento no Supabase: {e}")

# ==========================================
# ABA 3: ASSISTENTE DE INTELIGÊNCIA ARTIFICIAL
# ==========================================
with aba3:
    st.header("🤖 Assistente de IA para Clientes")
    st.write("Gere mensagens personalizadas de confirmação para enviar aos clientes via WhatsApp.")

    cliente_ia = st.text_input("Nome do Cliente para a Mensagem")
    veiculo_ia = st.text_input("Modelo do Carro")
    horario_ia = st.selectbox("Horário do Agendamento", ["08:30", "10:00", "11:30", "13:30", "15:00", "16:30"], key="ia_horario")

    if st.button("Gerar Mensagem de WhatsApp com IA"):
        if cliente_ia and veiculo_ia:
            mensagem_gerada = f"""*Olá, {cliente_ia}!* Aqui é do *Lava Rápido Sorocaba Clean*. 🚗✨
Passando para confirmar o agendamento da lavagem do seu *{veiculo_ia}* hoje às *{horario_ia}*. 
Nosso endereço é Rua Principal, Sorocaba - SP. Estamos te esperando! 🧼💧"""
            
            st.success("Mensagem gerada com sucesso pela IA:")
            st.code(mensagem_gerada, language="markdown")
        else:
            st.warning("Por favor, preencha o nome do cliente e o modelo do carro acima.")
