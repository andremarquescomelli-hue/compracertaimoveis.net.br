from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Lead, Interacao, Matricula, AnuncioPortal, Imovel, ImovelFoto, Lembrete
from scrapers import buscar_imoveis, buscar_todos_portais
from scrapers.enriquecedor import sugerir_telefones, buscar_whatsapp, extrair_telefones_texto
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui-mude-depois')
app.config['SENHA_CRM'] = 'imoveis2026'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{os.path.join(BASE_DIR, "imoveis_crm.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('imovel')]
    with db.engine.connect() as conn:
        if 'visualizacoes' not in cols:
            conn.execute(text('ALTER TABLE imovel ADD COLUMN visualizacoes INTEGER DEFAULT 0'))
        if 'destaque' not in cols:
            conn.execute(text('ALTER TABLE imovel ADD COLUMN destaque BOOLEAN DEFAULT 0'))
        # Criar tabela lembretes se nao existir
        if not inspector.has_table('lembrete'):
            conn.execute(text('''
                CREATE TABLE lembretes (
                    id INTEGER PRIMARY KEY,
                    titulo VARCHAR(200) NOT NULL,
                    cliente_nome VARCHAR(100),
                    cliente_telefone VARCHAR(20),
                    imovel_id INTEGER,
                    data_visita DATETIME NOT NULL,
                    local VARCHAR(200),
                    observacoes TEXT,
                    lembrado BOOLEAN DEFAULT 0,
                    criado_em DATETIME
                )
            '''))
            conn.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == app.config['SENHA_CRM']:
            session['logado'] = True
            return redirect(url_for('index'))
        else:
            flash('Senha incorreta!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/bot')
def bot_publico():
    return render_template('publico_bot.html')

@app.route('/')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    total_leads = Lead.query.count()
    total_matriculas = Matricula.query.count()
    total_anuncios = AnuncioPortal.query.count()
    total_imoveis = Imovel.query.count()
    leads_novos = Lead.query.filter_by(status='novo').count()
    matriculas_pendentes = Matricula.query.filter_by(situacao='pendente').count()
    ultimos_leads = Lead.query.order_by(Lead.criado_em.desc()).limit(5).all()
    return render_template('dashboard.html',
                          total_leads=total_leads,
                          total_matriculas=total_matriculas,
                          total_anuncios=total_anuncios,
                          total_imoveis=total_imoveis,
                          leads_novos=leads_novos,
                          matriculas_pendentes=matriculas_pendentes,
                          ultimos_leads=ultimos_leads)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== CRM - LEADS ====================

@app.route('/leads')
@login_required
def listar_leads():
    leads = Lead.query.order_by(Lead.criado_em.desc()).all()
    return render_template('leads.html', leads=leads)

@app.route('/leads/novo', methods=['GET', 'POST'])
@login_required
def novo_lead():
    if request.method == 'POST':
        lead = Lead(
            nome=request.form['nome'],
            telefone=request.form['telefone'],
            email=request.form.get('email'),
            origem=request.form.get('origem', 'manual'),
            status=request.form.get('status', 'novo'),
            interesse=request.form.get('interesse'),
            observacoes=request.form.get('observacoes')
        )
        db.session.add(lead)
        db.session.commit()
        flash('Lead cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_leads'))
    return render_template('lead_form.html', lead=None, title='Novo Lead')

@app.route('/leads/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_lead(id):
    lead = Lead.query.get_or_404(id)
    if request.method == 'POST':
        lead.nome = request.form['nome']
        lead.telefone = request.form['telefone']
        lead.email = request.form.get('email')
        lead.origem = request.form.get('origem')
        lead.status = request.form.get('status')
        lead.interesse = request.form.get('interesse')
        lead.observacoes = request.form.get('observacoes')
        db.session.commit()
        flash('Lead atualizado com sucesso!', 'success')
        return redirect(url_for('listar_leads'))
    return render_template('lead_form.html', lead=lead, title='Editar Lead')

@app.route('/leads/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_lead(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead excluído com sucesso!', 'success')
    return redirect(url_for('listar_leads'))

@app.route('/leads/<int:id>/interacao', methods=['POST'])
@login_required
def registrar_interacao(id):
    lead = Lead.query.get_or_404(id)
    interacao = Interacao(
        lead_id=lead.id,
        tipo=request.form['tipo'],
        descricao=request.form.get('descricao')
    )
    db.session.add(interacao)
    db.session.commit()
    flash('Interação registrada!', 'success')
    return redirect(url_for('ver_lead', id=id))

@app.route('/leads/<int:id>')
@login_required
def ver_lead(id):
    lead = Lead.query.get_or_404(id)
    interacoes = Interacao.query.filter_by(lead_id=id).order_by(Interacao.data.desc()).all()
    return render_template('lead_detalhes.html', lead=lead, interacoes=interacoes)

@app.route('/leads/buscar')
@login_required
def buscar_lead():
    termo = request.args.get('q', '')
    leads = Lead.query.filter(
        db.or_(
            Lead.nome.contains(termo),
            Lead.telefone.contains(termo),
            Lead.email.contains(termo)
        )
    ).all()
    return jsonify([{
        'id': l.id, 'nome': l.nome, 'telefone': l.telefone,
        'email': l.email, 'status': l.status, 'interesse': l.interesse
    } for l in leads])

# ==================== MATRÍCULAS ====================

@app.route('/matriculas')
@login_required
def listar_matriculas():
    matriculas = Matricula.query.order_by(Matricula.consulta_data.desc()).all()
    return render_template('matriculas.html', matriculas=matriculas)

@app.route('/matriculas/nova', methods=['GET', 'POST'])
@login_required
def nova_matricula():
    if request.method == 'POST':
        matricula = Matricula(
            imovel_endereco=request.form['imovel_endereco'],
            cartorio=request.form.get('cartorio'),
            numero_matricula=request.form.get('numero_matricula'),
            proprietario_nome=request.form.get('proprietario_nome'),
            proprietario_contato=request.form.get('proprietario_contato'),
            area=request.form.get('area'),
            valor=request.form.get('valor'),
            situacao=request.form.get('situacao', 'pendente'),
            observacoes=request.form.get('observacoes'),
            followup_data=datetime.strptime(request.form['followup_data'], '%Y-%m-%d') if request.form.get('followup_data') else None
        )
        db.session.add(matricula)
        db.session.commit()
        flash('Matrícula registrada com sucesso!', 'success')
        return redirect(url_for('listar_matriculas'))
    return render_template('matricula_form.html', matricula=None, title='Nova Matrícula')

@app.route('/matriculas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    if request.method == 'POST':
        matricula.imovel_endereco = request.form['imovel_endereco']
        matricula.cartorio = request.form.get('cartorio')
        matricula.numero_matricula = request.form.get('numero_matricula')
        matricula.proprietario_nome = request.form.get('proprietario_nome')
        matricula.proprietario_contato = request.form.get('proprietario_contato')
        matricula.area = request.form.get('area')
        matricula.valor = request.form.get('valor')
        matricula.situacao = request.form.get('situacao')
        matricula.observacoes = request.form.get('observacoes')
        matricula.followup_data = datetime.strptime(request.form['followup_data'], '%Y-%m-%d') if request.form.get('followup_data') else None
        db.session.commit()
        flash('Matrícula atualizada com sucesso!', 'success')
        return redirect(url_for('listar_matriculas'))
    return render_template('matricula_form.html', matricula=matricula, title='Editar Matrícula')

@app.route('/matriculas/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    db.session.delete(matricula)
    db.session.commit()
    flash('Matrícula excluída com sucesso!', 'success')
    return redirect(url_for('listar_matriculas'))

# ==================== SCRAPERS ====================

@app.route('/scrapers')
@login_required
def scrapers_page():
    return render_template('scrapers.html')

@app.route('/scrapers/buscar', methods=['POST'])
@login_required
def scraper_buscar():
    cidade = request.form.get('cidade', 'Assis-SP')
    tipo = request.form.get('tipo', 'venda')
    portais = request.form.getlist('portais')
    
    resultados = []
    
    if not cidade:
        flash('Informe uma cidade!', 'error')
        return redirect(url_for('scrapers_page'))
    
    for portal in portais:
        try:
            imoveis = buscar_imoveis(portal, cidade, tipo)
            for imovel in imoveis:
                anuncio = AnuncioPortal(
                    portal=imovel['portal'],
                    titulo=imovel['titulo'],
                    endereco=imovel.get('endereco'),
                    preco=imovel.get('preco'),
                    area=imovel.get('area'),
                    quartos=imovel.get('quartos'),
                    telefone=imovel.get('telefone'),
                    url=imovel.get('url'),
                    contato_nome=imovel.get('contato_nome'),
                    foto_url=imovel.get('foto_url')
                )
                db.session.add(anuncio)
            resultados.extend(imoveis)
        except Exception as e:
            flash(f'Erro ao buscar no {portal}: {str(e)}', 'error')
    
    db.session.commit()
    
    return render_template('scrapers_resultado.html', resultados=resultados, cidade=cidade)

@app.route('/scrapers/anuncios')
@login_required
def listar_anuncios():
    anuncios = AnuncioPortal.query.order_by(AnuncioPortal.importado_em.desc()).all()
    return render_template('anuncios.html', anuncios=anuncios)

@app.route('/scrapers/anuncio/<int:id>/converter', methods=['POST'])
@login_required
def converter_anuncio_lead(id):
    anuncio = AnuncioPortal.query.get_or_404(id)
    
    lead = Lead(
        nome=anuncio.contato_nome or 'Contato via Portal',
        telefone=anuncio.telefone or '',
        email='',
        origem=f"Portal: {anuncio.portal}",
        interesse=anuncio.titulo,
        observacoes=f"Endereço: {anuncio.endereco}\nPreço: {anuncio.preco}\nURL: {anuncio.url}"
    )
    db.session.add(lead)
    db.session.flush()
    
    anuncio.convertido_lead_id = lead.id
    db.session.commit()
    
    flash('Anúncio convertido em lead!', 'success')
    return redirect(url_for('ver_lead', id=lead.id))

# ==================== ENRIQUECIMENTO ====================

@app.route('/enriquecer/<int:id>', methods=['GET', 'POST'])
@login_required
def enriquecer_lead(id):
    lead = Lead.query.get_or_404(id)
    resultados = []
    
    if request.method == 'POST':
        nome = request.form.get('nome_busca', lead.nome)
        cidade = request.form.get('cidade_busca', 'Assis')
        
        resultados = sugerir_telefones(nome, cidade)
        
        for r in resultados:
            interacao = Interacao(
                lead_id=lead.id,
                tipo='pesquisa',
                descricao=f"Pesquisa: {r['fonte']} - {r.get('titulo', '')[:150]}"
            )
            db.session.add(interacao)
        db.session.commit()
    
    return render_template('enriquecer.html', lead=lead, resultados=resultados)

@app.route('/whatsapp/<int:id>')
@login_required
def whatsapp_lead(id):
    lead = Lead.query.get_or_404(id)
    if lead.telefone:
        url = buscar_whatsapp(lead.telefone)
        return redirect(url)
    flash('Lead sem telefone cadastrado.', 'error')
    return redirect(url_for('ver_lead', id=id))

@app.route('/enriquecer/matricula/<int:id>', methods=['GET', 'POST'])
@login_required
def enriquecer_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    resultados = []
    
    if request.method == 'POST':
        nome = request.form.get('nome_busca', matricula.proprietario_nome)
        cidade = request.form.get('cidade_busca', 'Assis')
        
        if nome:
            resultados = sugerir_telefones(nome, cidade)
        else:
            flash('Informe o nome do proprietário.', 'error')
    
    return render_template('enriquecer_matricula.html', matricula=matricula, resultados=resultados)

# ==================== IMÓVEIS ====================

@app.route('/imoveis')
@login_required
def listar_imoveis():
    imoveis = Imovel.query.order_by(Imovel.criado_em.desc()).all()
    return render_template('imoveis.html', imoveis=imoveis)

@app.route('/imoveis/novo', methods=['GET', 'POST'])
@login_required
def novo_imovel():
    if request.method == 'POST':
        imovel = Imovel(
            titulo=request.form['titulo'],
            tipo=request.form.get('tipo'),
            negocio=request.form.get('negocio'),
            endereco=request.form['endereco'],
            bairro=request.form.get('bairro'),
            cidade=request.form.get('cidade', 'Assis-SP'),
            cep=request.form.get('cep'),
            preco=request.form.get('preco'),
            area=request.form.get('area'),
            quartos=request.form.get('quartos'),
            banheiros=request.form.get('banheiros'),
            vagas=request.form.get('vagas'),
            descricao=request.form.get('descricao'),
            proprietario_nome=request.form.get('proprietario_nome'),
            proprietario_telefone=request.form.get('proprietario_telefone'),
            proprietario_email=request.form.get('proprietario_email'),
            status=request.form.get('status', 'ativo')
        )
        
        fotos = request.files.getlist('fotos')
        for i, file in enumerate(fotos):
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto = ImovelFoto(
                    caminho=f'/static/uploads/{filename}',
                    ordem=i
                )
                imovel.fotos.append(foto)
                if i == 0:
                    imovel.foto_capa = f'/static/uploads/{filename}'
        
        db.session.add(imovel)
        db.session.commit()
        flash('Imóvel cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_imoveis'))
    return render_template('imovel_form.html', imovel=None, title='Novo Imóvel')

@app.route('/imoveis/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    if request.method == 'POST':
        imovel.titulo = request.form['titulo']
        imovel.tipo = request.form.get('tipo')
        imovel.negocio = request.form.get('negocio')
        imovel.endereco = request.form['endereco']
        imovel.bairro = request.form.get('bairro')
        imovel.cidade = request.form.get('cidade', 'Assis-SP')
        imovel.cep = request.form.get('cep')
        imovel.preco = request.form.get('preco')
        imovel.area = request.form.get('area')
        imovel.quartos = request.form.get('quartos')
        imovel.banheiros = request.form.get('banheiros')
        imovel.vagas = request.form.get('vagas')
        imovel.descricao = request.form.get('descricao')
        imovel.proprietario_nome = request.form.get('proprietario_nome')
        imovel.proprietario_telefone = request.form.get('proprietario_telefone')
        imovel.proprietario_email = request.form.get('proprietario_email')
        imovel.status = request.form.get('status', 'ativo')
        
        fotos = request.files.getlist('fotos')
        for file in fotos:
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto = ImovelFoto(
                    caminho=f'/static/uploads/{filename}',
                    ordem=len(imovel.fotos)
                )
                imovel.fotos.append(foto)
                if not imovel.foto_capa:
                    imovel.foto_capa = f'/static/uploads/{filename}'
        
        db.session.commit()
        flash('Imóvel atualizado com sucesso!', 'success')
        return redirect(url_for('listar_imoveis'))
    return render_template('imovel_form.html', imovel=imovel, title='Editar Imóvel')

@app.route('/imovel/<int:id>')
def ver_imovel_publico(id):
    imovel = Imovel.query.get_or_404(id)
    # Incrementa visualizacao
    imovel.visualizacoes = (imovel.visualizacoes or 0) + 1
    db.session.commit()
    fotos = ImovelFoto.query.filter_by(imovel_id=id).order_by(ImovelFoto.ordem).all()
    return render_template('imovel_publico.html', imovel=imovel, fotos=fotos)

@app.route('/imoveis/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    for foto in imovel.fotos:
        foto_path = os.path.join(BASE_DIR, foto.caminho.lstrip('/'))
        if os.path.exists(foto_path):
            os.remove(foto_path)
    if imovel.foto_capa:
        foto_path = os.path.join(BASE_DIR, imovel.foto_capa.lstrip('/'))
        if os.path.exists(foto_path):
            os.remove(foto_path)
    db.session.delete(imovel)
    db.session.commit()
    flash('Imóvel excluído com sucesso!', 'success')
    return redirect(url_for('listar_imoveis'))

@app.route('/imoveis/<int:id>/foto/<int:foto_id>/excluir', methods=['POST'])
@login_required
def excluir_foto(id, foto_id):
    imovel = Imovel.query.get_or_404(id)
    foto = ImovelFoto.query.get_or_404(foto_id)
    
    if foto.caminho == imovel.foto_capa:
        imovel.foto_capa = None
    
    foto_path = os.path.join(BASE_DIR, foto.caminho.lstrip('/'))
    if os.path.exists(foto_path):
        os.remove(foto_path)
    
    db.session.delete(foto)
    
    if not imovel.foto_capa and imovel.fotos:
        imovel.foto_capa = imovel.fotos[0].caminho
    
    db.session.commit()
    flash('Foto excluída!', 'success')
    return redirect(url_for('ver_imovel', id=id))

@app.route('/imoveis/<int:id>/fotos/reorder', methods=['POST'])
@login_required
def reorder_fotos(id):
    imovel = Imovel.query.get_or_404(id)
    data = request.get_json()
    new_order = data.get('order', [])
    
    for i, foto_id in enumerate(new_order):
        foto = ImovelFoto.query.get(foto_id)
        if foto and foto.imovel_id == id:
            foto.ordem = i
    
    if new_order:
        first_foto = ImovelFoto.query.get(new_order[0])
        if first_foto:
            imovel.foto_capa = first_foto.caminho
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/imoveis/<int:id>/compartilhar')
@login_required
def compartilhar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    fotos = ImovelFoto.query.filter_by(imovel_id=id).order_by(ImovelFoto.ordem).all()
    return render_template('compartilhar.html', imovel=imovel, fotos=fotos)

@app.route('/publico')
def imoveis_publico():
    imoveis = Imovel.query.filter_by(status='ativo').order_by(Imovel.criado_em.desc()).all()
    fotos_por_imovel = {}
    for imovel in imoveis:
        fotos = ImovelFoto.query.filter_by(imovel_id=imovel.id).order_by(ImovelFoto.ordem).all()
        fotos_por_imovel[imovel.id] = fotos
    return render_template('publico.html', imoveis=imoveis, fotos_por_imovel=fotos_por_imovel)

# ==================== API ====================

@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify({
        'total_leads': Lead.query.count(),
        'leads_novos': Lead.query.filter_by(status='novo').count(),
        'leads_contato': Lead.query.filter_by(status='em_contato').count(),
        'leads_visita': Lead.query.filter_by(status='visita_agendada').count(),
        'leads_proposta': Lead.query.filter_by(status='proposta').count(),
        'total_matriculas': Matricula.query.count(),
        'matriculas_pendentes': Matricula.query.filter_by(situacao='pendente').count(),
        'total_anuncios': AnuncioPortal.query.count()
    })

# ==================== LEMBRETES DE VISITA ====================

@app.route('/lembretes')
@login_required
def listar_lembretes():
    from datetime import datetime
    lembretes = Lembrete.query.order_by(Lembrete.data_visita.asc()).all()
    imoveis = Imovel.query.filter_by(status='ativo').all()
    return render_template('lembretes.html', lembretes=lembretes, imoveis=imoveis)

@app.route('/lembretes/novo', methods=['GET', 'POST'])
@login_required
def novo_lembrete():
    if request.method == 'POST':
        from datetime import datetime
        data_str = request.form.get('data_visita')
        hora_str = request.form.get('hora_visita')
        data_visita = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
        
        lembrete = Lembrete(
            titulo=request.form.get('titulo'),
            cliente_nome=request.form.get('cliente_nome'),
            cliente_telefone=request.form.get('cliente_telefone'),
            corretor_nome=request.form.get('corretor_nome') or 'Andre Comelli',
            corretor_telefone=request.form.get('corretor_telefone') or '(18) 99762-8360',
            imovel_id=request.form.get('imovel_id') or None,
            data_visita=data_visita,
            local=request.form.get('local'),
            observacoes=request.form.get('observacoes'),
            lembrado=False
        )
        db.session.add(lembrete)
        db.session.commit()
        
        # Envia WhatsApp imediatamente ao criar
        from datetime import timedelta
        import urllib.parse
        import subprocess
        import threading
        import time
        import os
        
        data_formatada = data_visita.strftime('%d/%m/%Y às %H:%M')
        imovel_endereco = ''
        if lembrete.imovel:
            imovel_endereco = f"{lembrete.imovel.endereco}, {lembrete.imovel.bairro} - {lembrete.imovel.cidade}"
        
        texto = f"""🔔 *LEMBRETE CRIADO - Compra Certa Imóveis*

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA DA VISITA:* {data_formatada}
📍 *LOCAL:* {lembrete.local or imovel_endereco or 'A combinar'}

🏠 *IMÓVEL:*
{lembrete.imovel.titulo if lembrete.imovel else 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {lembrete.cliente_nome or 'Não informado'}
Telefone: {lembrete.cliente_telefone or 'Não informado'}

👔 *DADOS DO CORRETOR:*
Nome: {lembrete.corretor_nome or 'Andre Comelli'}
Telefone: {lembrete.corretor_telefone or '(18) 99762-8360'}

📝 *OBSERVAÇÕES:*
{lembrete.observacoes or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *VISITA AGENDADA - NÃO ESQUEÇA!*

Compra Certa Imóveis
(18) 99762-8360"""
        
        texto_encoded = urllib.parse.quote(texto)
        
        def formatar_telefone(telefone):
            tel_limpo = ''.join(filter(str.isdigit, telefone or ''))
            if tel_limpo.startswith('0'):
                tel_limpo = '55' + tel_limpo[2:]
            elif not tel_limpo.startswith('55'):
                tel_limpo = '55' + tel_limpo
            return tel_limpo if len(tel_limpo) >= 12 else ''
        
        def enviar_para_cliente():
            time.sleep(8)
            tel = formatar_telefone(lembrete.cliente_telefone)
            if tel:
                url = f"https://web.whatsapp.com/send?phone={tel}&text={texto_encoded}"
                subprocess.Popen(['start', '', url], shell=True)
                time.sleep(3)
                subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        def enviar_para_corretor():
            time.sleep(15)
            tel = formatar_telefone(lembrete.corretor_telefone)
            if tel:
                url = f"https://web.whatsapp.com/send?phone={tel}&text={texto_encoded}"
                subprocess.Popen(['start', '', url], shell=True)
                time.sleep(8)
                subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        # Envia para ambos imediatamente
        threading.Thread(target=enviar_para_cliente, daemon=True).start()
        threading.Thread(target=enviar_para_corretor, daemon=True).start()
        
        # Calcula tempo até o envio automático (3 horas antes)
        tempo_ate_visita = (data_visita - datetime.now()).total_seconds()
        horas_ate_visita = tempo_ate_visita / 3600
        
        if horas_ate_visita > 3:
            flash(f'Lembrete criado e WhatsApp enviado para CLIENTE e CORRETOR! Novo aviso 3h antes da visita.', 'success')
        else:
            flash(f'Lembrete criado e WhatsApp enviado! (Menos de 3h para visita)', 'success')
        
        return redirect(url_for('listar_lembretes'))
    
    imoveis = Imovel.query.filter_by(status='ativo').all()
    return render_template('lembrete_form.html', lembrete=None, imoveis=imoveis)

@app.route('/lembretes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_lembrete(id):
    lembrete = Lembrete.query.get_or_404(id)
    if request.method == 'POST':
        from datetime import datetime
        data_str = request.form.get('data_visita')
        hora_str = request.form.get('hora_visita')
        lembrete.titulo = request.form.get('titulo')
        lembrete.cliente_nome = request.form.get('cliente_nome')
        lembrete.cliente_telefone = request.form.get('cliente_telefone')
        lembrete.corretor_nome = request.form.get('corretor_nome') or 'Andre Comelli'
        lembrete.corretor_telefone = request.form.get('corretor_telefone') or '(18) 99762-8360'
        lembrete.imovel_id = request.form.get('imovel_id') or None
        lembrete.data_visita = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
        lembrete.local = request.form.get('local')
        lembrete.observacoes = request.form.get('observacoes')
        db.session.commit()
        
        # Envia WhatsApp ao atualizar
        import urllib.parse
        import subprocess
        import threading
        import time
        import os
        
        data_formatada = lembrete.data_visita.strftime('%d/%m/%Y às %H:%M')
        imovel_endereco = ''
        if lembrete.imovel:
            imovel_endereco = f"{lembrete.imovel.endereco}, {lembrete.imovel.bairro} - {lembrete.imovel.cidade}"
        
        texto = f"""🔔 *LEMBRETE ATUALIZADO - Compra Certa Imóveis*

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA DA VISITA:* {data_formatada}
📍 *LOCAL:* {lembrete.local or imovel_endereco or 'A combinar'}

🏠 *IMÓVEL:*
{lembrete.imovel.titulo if lembrete.imovel else 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {lembrete.cliente_nome or 'Não informado'}
Telefone: {lembrete.cliente_telefone or 'Não informado'}

👔 *DADOS DO CORRETOR:*
Nome: {lembrete.corretor_nome or 'Andre Comelli'}
Telefone: {lembrete.corretor_telefone or '(18) 99762-8360'}

📝 *OBSERVAÇÕES:*
{lembrete.observacoes or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *VISITA AGENDADA - NÃO ESQUEÇA!*

Compra Certa Imóveis
(18) 99762-8360"""
        
        texto_encoded = urllib.parse.quote(texto)
        
        def formatar_telefone(telefone):
            tel_limpo = ''.join(filter(str.isdigit, telefone or ''))
            if tel_limpo.startswith('0'):
                tel_limpo = '55' + tel_limpo[2:]
            elif not tel_limpo.startswith('55'):
                tel_limpo = '55' + tel_limpo
            return tel_limpo if len(tel_limpo) >= 12 else ''
        
        def enviar_para_cliente():
            time.sleep(8)
            tel = formatar_telefone(lembrete.cliente_telefone)
            if tel:
                url = f"https://web.whatsapp.com/send?phone={tel}&text={texto_encoded}"
                subprocess.Popen(['start', '', url], shell=True)
                time.sleep(3)
                subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        def enviar_para_corretor():
            time.sleep(15)
            tel = formatar_telefone(lembrete.corretor_telefone)
            if tel:
                url = f"https://web.whatsapp.com/send?phone={tel}&text={texto_encoded}"
                subprocess.Popen(['start', '', url], shell=True)
                time.sleep(8)
                subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        threading.Thread(target=enviar_para_cliente, daemon=True).start()
        threading.Thread(target=enviar_para_corretor, daemon=True).start()
        
        flash('Lembrete atualizado e WhatsApp enviado para CLIENTE e CORRETOR!', 'success')
        return redirect(url_for('listar_lembretes'))
    
    imoveis = Imovel.query.filter_by(status='ativo').all()
    return render_template('lembrete_form.html', lembrete=lembrete, imoveis=imoveis)

@app.route('/lembretes/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_lembrete(id):
    lembrete = Lembrete.query.get_or_404(id)
    db.session.delete(lembrete)
    db.session.commit()
    flash('Lembrete excluído!', 'success')
    return redirect(url_for('listar_lembretes'))

@app.route('/lembretes/<int:id>/whatsapp')
@login_required
def whatsapp_lembrete(id):
    lembrete = Lembrete.query.get_or_404(id)
    from datetime import datetime
    import urllib.parse
    import subprocess
    import threading
    import time
    import os
    
    data_formatada = lembrete.data_visita.strftime('%d/%m/%Y às %H:%M')
    imovel_endereco = ''
    if lembrete.imovel:
        imovel_endereco = f"{lembrete.imovel.endereco}, {lembrete.imovel.bairro} - {lembrete.imovel.cidade}"
    
    texto = f"""🔔 *LEMBRETE DE VISITA - Compra Certa Imóveis*

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA:* {data_formatada}
📍 *LOCAL:* {lembrete.local or imovel_endereco or 'A combinar'}

🏠 *IMÓVEL:*
{lembrete.imovel.titulo if lembrete.imovel else 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {lembrete.cliente_nome or 'Não informado'}
Telefone: {lembrete.cliente_telefone or 'Não informado'}

👔 *DADOS DO CORRETOR:*
Nome: {lembrete.corretor_nome or 'Andre Comelli'}
Telefone: {lembrete.corretor_telefone or '(18) 99762-8360'}

📝 *OBSERVAÇÕES:*
{lembrete.observacoes or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *NÃO ESQUEÇA DA VISITA!*

Obrigado pela atenção!
Compra Certa Imóveis
(18) 99762-8360"""

    texto_encoded = urllib.parse.quote(texto)
    
    # Telefone do cliente
    telefone_cliente = ''
    if lembrete.cliente_telefone:
        tel_limpo = ''.join(filter(str.isdigit, lembrete.cliente_telefone))
        if tel_limpo.startswith('0'):
            tel_limpo = '55' + tel_limpo[2:]
        elif not tel_limpo.startswith('55'):
            tel_limpo = '55' + tel_limpo
        if len(tel_limpo) >= 12:
            telefone_cliente = tel_limpo
    
    # Telefone do corretor
    telefone_corretor = ''
    if lembrete.corretor_telefone:
        tel_limpo = ''.join(filter(str.isdigit, lembrete.corretor_telefone))
        if tel_limpo.startswith('0'):
            tel_limpo = '55' + tel_limpo[2:]
        elif not tel_limpo.startswith('55'):
            tel_limpo = '55' + tel_limpo
        if len(tel_limpo) >= 12:
            telefone_corretor = tel_limpo
    
    def enviar_para_cliente():
        time.sleep(8)
        if telefone_cliente:
            url_cliente = f"https://web.whatsapp.com/send?phone={telefone_cliente}&text={texto_encoded}"
            subprocess.Popen(['start', '', url_cliente], shell=True)
            time.sleep(3)
            subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    def enviar_para_corretor():
        time.sleep(15)
        if telefone_corretor:
            url_corretor = f"https://web.whatsapp.com/send?phone={telefone_corretor}&text={texto_encoded}"
            subprocess.Popen(['start', '', url_corretor], shell=True)
            time.sleep(8)
            subprocess.Popen(['python', 'clicar_enviar.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    # Envia para ambos
    threading.Thread(target=enviar_para_cliente, daemon=True).start()
    threading.Thread(target=enviar_para_corretor, daemon=True).start()
    
    flash('Enviando lembrete para CLIENTE e CORRETOR!', 'success')
    return redirect(url_for('listar_lembretes'))

@app.route('/lembretes/<int:id>/whatsapp-proprio')
@login_required
def whatsapp_lembrete_proprio(id):
    """Envia lembrete para o número do corretor"""
    lembrete = Lembrete.query.get_or_404(id)
    from datetime import datetime
    data_formatada = lembrete.data_visita.strftime('%d/%m/%Y às %H:%M')
    imovel_endereco = ''
    if lembrete.imovel:
        imovel_endereco = f"{lembrete.imovel.endereco}, {lembrete.imovel.bairro} - {lembrete.imovel.cidade}"
    
    texto = f"""🔔 *LEMBRETE DE VISITA - Compra Certa Imóveis*

━━━━━━━━━━━━━━━━━━━━━━━━

📅 *DATA:* {data_formatada}
📍 *LOCAL:* {lembrete.local or imovel_endereco or 'A combinar'}

🏠 *IMÓVEL:*
{lembrete.imovel.titulo if lembrete.imovel else 'Não informado'}

👤 *DADOS DO CLIENTE:*
Nome: {lembrete.cliente_nome or 'Não informado'}
Telefone: {lembrete.cliente_telefone or 'Não informado'}

📝 *OBSERVAÇÕES:*
{lembrete.observacoes or 'Sem observações'}

━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *NÃO ESQUEÇA DA VISITA!*

Obrigado pela atenção!
Compra Certa Imóveis
(18) 99762-8360"""

    import urllib.parse
    texto_encoded = urllib.parse.quote(texto)
    url = f"https://web.whatsapp.com/send?phone=5518997628360&text={texto_encoded}"
    
    # Abre WhatsApp e clica automaticamente
    import subprocess
    import threading
    import time
    import os
    
    def abrir_e_enviar():
        time.sleep(8)
        try:
            subprocess.Popen(['python', 'clicar_enviar.py'], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
        except:
            pass
    
    threading.Thread(target=abrir_e_enviar, daemon=True).start()
    return redirect(url)

@app.route('/bot-comandos')
@login_required
def bot_comandos():
    return render_template('bot_comandos.html')

@app.route('/api/enviar-comando', methods=['POST'])
@login_required
def api_enviar_comando():
    from bot_whatsapp import processar_comando
    import json
    
    data = request.get_json()
    comando = data.get('comando', '')
    
    resultado = processar_comando(comando)
    
    return jsonify({'resposta': resultado, 'comando': comando})

@app.route('/api/lembretes-proximos')
@login_required
def api_lembretes_proximos():
    from datetime import datetime, timedelta
    agora = datetime.now()
    limite = agora + timedelta(hours=24)
    proximos = Lembrete.query.filter(
        Lembrete.data_visita >= agora,
        Lembrete.data_visita <= limite,
        Lembrete.lembrado == False
    ).order_by(Lembrete.data_visita.asc()).all()
    return jsonify([{
        'id': l.id,
        'titulo': l.titulo,
        'cliente': l.cliente_nome,
        'data': l.data_visita.strftime('%d/%m às %H:%M'),
        'imovel': l.imovel.titulo if l.imovel else ''
    } for l in proximos])

@app.route('/avisos')
@login_required
def pagina_avisos():
    from datetime import datetime, timedelta
    agora = datetime.now()
    limite = agora + timedelta(hours=24)
    
    lembretes_proximos = Lembrete.query.filter(
        Lembrete.data_visita >= agora,
        Lembrete.data_visita <= limite
    ).order_by(Lembrete.data_visita.asc()).all()
    
    todos_lembretes = Lembrete.query.filter(
        Lembrete.data_visita >= agora
    ).order_by(Lembrete.data_visita.asc()).limit(20).all()
    
    for lembrete in lembretes_proximos:
        diff = (lembrete.data_visita - agora).total_seconds() / 3600
        lembrete.urgente = diff < 1
        lembrete.proximo = 1 <= diff <= 3
    
    return render_template('avisos.html', 
                          lembretes_proximos=lembretes_proximos,
                          todos_lembretes=todos_lembretes,
                          agora=agora)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
