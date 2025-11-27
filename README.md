AppFit – Sistema de Registro de Treinos

O AppFit é um sistema em Python integrado ao MySQL, usado para registrar treinos, calcular IMC/TMB e exibir histórico de atividades.

🔧 Tecnologias

Python 3

MySQL

mysql-connector-python

📌 Funcionalidades

Login e criação de usuário

Registro de exercícios

Cardio (corrida, caminhada, natação, ciclismo)

Musculação (peso, repetições, séries)

Cálculo de IMC e TMB

Histórico dos últimos 10 exercícios

Cálculo automático de gasto calórico

🗄 Banco de Dados

Banco: AppFit
Tabelas principais:

usuario – dados do usuário

ficha – registros de musculação

atv_cardio – atividades de cardio

historico – últimos exercícios realizados

Execute os comandos SQL incluídos no arquivo para criar as tabelas.

▶️ Como executar

Instale o conector:

pip install mysql-connector-python


Configure as credenciais MySQL no código.

Execute o script:

python appfit.py
