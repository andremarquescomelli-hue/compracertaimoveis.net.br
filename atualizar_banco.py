from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE lembrete ADD COLUMN corretor_nome VARCHAR(100)'))
        db.session.commit()
        print('Coluna corretor_nome adicionada')
    except Exception as e:
        print(f'Erro corretor_nome: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE lembrete ADD COLUMN corretor_telefone VARCHAR(20)'))
        db.session.commit()
        print('Coluna corretor_telefone adicionada')
    except Exception as e:
        print(f'Erro corretor_telefone: {e}')

print('Atualizacao concluida!')
