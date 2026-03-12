# 📊 FinOps Personal 

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)

Um sistema financeiro pessoal robusto e elegante construído com Python. Desenvolvido com foco em **UI/UX Premium** (Dark Mode vetorial) e **regras de negócio estritas**, garantindo que a matemática do usuário seja sempre fiel à realidade.

<img width="1868" height="878" alt="image" src="https://i.imgur.com/mgCX52O.png" />


---

<img width="1868" height="878" alt="image" src="https://i.imgur.com/NI6dFDC.png" />

---


## 🚀 Principais Funcionalidades

Diferente de planilhas simples, o FinOps Personal atua como um motor contábil, possuindo inteligência para barrar ações inválidas e automatizar fluxos longos:

* **Motor de Cartões de Crédito:** Controle de limites em tempo real. O sistema calcula automaticamente o limite disponível subtraindo compras agendadas e somando faturas pagas.
* **Assinaturas e Parcelamentos:** Geração automática de despesas futuras (ex: compras em 12x ou assinaturas fixas anuais) com apenas um clique.
* **Gestão de Faturas em Lote (Bulk Actions):** Fechamento e pagamento da fatura completa de um cartão com um único clique, liberando o limite instantaneamente.
* **Sistema de "Caixinha" Blindado:** Travas de segurança que impedem o usuário de guardar dinheiro usando limite de crédito ou resgatar valores maiores do que o guardado.
* **Alertas Inteligentes:** O painel rastreia a base de dados diariamente e notifica (UI Toasts e Banners) sobre faturas a vencer nos próximos 5 dias ou contas em atraso.
* **Exportação de Relatórios:** Geração instantânea de relatórios formatados em PDF e planilhas em CSV.

---

##  Arquitetura do Sistema (MVC)

O projeto foi estruturado utilizando o padrão de separação de responsabilidades (Model-View-Controller adaptado), garantindo um **código limpo, escalável e de fácil manutenção**.

| Camada | Arquivo | Responsabilidade |
| :--- | :--- | :--- |
| **View** | `app.py` | Interface do usuário (Streamlit). Focada apenas em renderizar componentes, gráficos Plotly e coletar inputs. |
| **Controller** | `controllers.py` | O "Cérebro". Contém todas as validações, regras de negócio (limites, saldo negativo) e lógica de datas antes de acionar o banco. |
| **Model** | `database.py` | Camada de abstração de dados. Gerencia a conexão com o Supabase, queries e autenticação (Auth). |
| **Assets** | `utils.py` | Dicionário de SVGs embutidos e injeção de CSS global (Clean UI). |

---

## 🛡️ Regras de Negócio Implementadas

Para garantir a integridade contábil, o sistema possui travas rígidas:
1. **Prevenção de Saldo Negativo:** O sistema bloqueia transações em Dinheiro/Pix se o "Saldo Geral" for insuficiente.
2. **Separação de Regimes:** O painel diferencia o *Regime de Caixa* (dinheiro que já saiu da conta) do *Regime de Competência* (poder aquisitivo gasto no mês, mostrado nos gráficos), evitando dupla contagem ao pagar faturas.
3. **Empty States:** Tratamento robusto para novos usuários, garantindo que a interface se adapte elegantemente quando o banco de dados está vazio.

---

## 💻 Como rodar o projeto localmente

1. Clone o repositório
   git clone [https://github.com/JohnDevCoda/finops-personal.git](https://github.com/JohnDevCoda/finops-personal.git)
   
    cd finops-personal
   
3. Instale as dependênciasCertifique-se de ter o Python 3.10+ instalado.

    pip install -r requirements.txt
   
(O arquivo requirements.txt deve conter as bibliotecas descritas no projeto)

5. Configure as Variáveis de AmbienteCrie uma pasta chamada .streamlit na raiz do projeto e dentro dela crie um arquivo secrets.toml.
Insira suas credenciais do Supabase:

**Ini, TOML**

**SUPABASE_URL** = "sua-url-aqui"

**SUPABASE_KEY** = "sua-anon-key-aqui"

5. Inicie a aplicação

   **streamlit run app.py**

   ---
   
👨‍💻 Autor Jonathan (DevJonathanSantana) Estudante de Análise e Desenvolvimento de Sistemas na Estácio | Desenvolvedor Front-end

   <a href="https://www.linkedin.com/in/jonathan-santana-544747322" target="_blank">
        <img
          alt="LinkedIn
          title="Me siga no LinkedIn
          src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" target="_blank"
          />


