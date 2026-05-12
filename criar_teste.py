from app import app, db, Lembrete
from datetime import datetime, timedelta

with app.app_context():
    data_teste = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    lembrete = Lembrete(
        titulo='Teste Automatico',
        cliente_nome='Cliente Teste',
        cliente_telefone='(18) 99999-9999',
        corretor_nome='Andre Comelli',
        corretor_telefone='(18) 99762-8360',
        data_visita=data_teste,
        local='Rua Teste, Centro - Assis',
        observacoes='Este e um lembrete de TESTE automatico',
        lembrado=False
    )
    db.session.add(lembrete)
    db.session.commit()
    
    print('=' * 50)
    print('LEMbrete de TESTE criado!')
    print('=' * 50)
    print('Titulo: ' + lembrete.titulo)
    print('Data: ' + lembrete.data_visita.strftime('%d/%m/%Y as %H:%M'))
    horas = (data_teste - datetime.now()).total_seconds() / 3600
    print('Horas ate a visita: ' + str(horas) + 'h')
    print()
    print('O sistema enviara WhatsApp automaticamente 3 horas antes!')
    print('=' * 50)
