#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatório de criativos dos cursos presenciais da Delva/HOF (Especialização + Imersão Iniciantes).
Fonte: dados.json (dump da Graph API, nível anúncio, date_preset=maximum)."""
import json, os, html, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados.json')))

def brl(v):
    return ('R$ ' + f'{v:,.2f}').replace(',', 'X').replace('.', ',').replace('X', '.')

def img_espec(n):
    p = f'/criativos/hof-presencial/hof_espec_{n}.png'
    st = f'/criativos/hof-presencial/hof_story_{n}.png'
    if not os.path.exists(BASE + '/../..' + st.replace('/criativos', '/criativos')):
        pass
    return p, st

REPO = os.path.abspath(os.path.join(BASE, '..', '..'))
def existe(rel):
    return os.path.exists(os.path.join(REPO, rel.lstrip('/')))

def artes(curso, nome):
    if curso == 'ESPEC':
        n = nome.split('_')[-1]
        feed = f'/criativos/hof-presencial/hof_espec_{n}.png'
        story = f'/criativos/hof-presencial/hof_story_{n}.png'
        if not existe(story):
            story = f'/criativos/hof-presencial/hof_story_{n}.jpg'
    else:
        n = int(nome.split('_')[-1])
        feed = f'/criativos/hof-imersao/imersao_feed_{n}.jpg'
        story = f'/criativos/hof-imersao/imersao_story_{n}.jpg'
    return (feed if existe(feed) else None), (story if existe(story) else None)

def gancho(body):
    return body.strip().split('\n')[0].strip()

def cards(curso):
    rows = [dict(nome=k, **v) for k, v in D[curso].items() if 'spend' in v]
    rows.sort(key=lambda r: (r['conv'] == 0, r['spend'] / r['conv'] if r['conv'] else -r['spend']))
    out = []
    for i, r in enumerate(rows):
        feed, story = artes(curso, r['nome'])
        cpc = r['spend'] / r['conv'] if r['conv'] else None
        publico = ''
        if curso == 'IMERSAO':
            publico = 'Odonto' if 'ODONTO' in r['nome'] else 'Mix saúde'
        medalha = ''
        if r['conv'] and i == 0: medalha = 'Melhor custo'
        elif r['conv'] == 0: medalha = 'Sem conversa'
        num = r['nome'].split('_')[-1]
        out.append(f'''
<article class="cr{' vence' if medalha=='Melhor custo' else ''}{' zero' if r['conv']==0 else ''}">
  <a class="cr-img" href="{feed}" target="_blank" rel="noopener">
    <img src="{feed}" alt="Criativo {html.escape(r['nome'])}" loading="lazy" width="900" height="900">
  </a>
  <div class="cr-corpo">
    <div class="cr-top">
      <span class="cr-id">#{num}{(' · ' + publico) if publico else ''}</span>
      {f'<span class="pin">{medalha}</span>' if medalha else ''}
    </div>
    <h4>{html.escape(r['title'])}</h4>
    <p class="cr-gancho">{html.escape(gancho(r['body']))}</p>
    <div class="cr-num">
      <div><b>{brl(cpc) if cpc else '—'}</b><span>por conversa</span></div>
      <div><b>{r['conv']:.0f}</b><span>conversas</span></div>
      <div><b>{brl(r['spend'])}</b><span>investido</span></div>
      <div><b>{r['ctr']:.2f}%</b><span>CTR</span></div>
      <div><b>{brl(r['cpm'])}</b><span>CPM</span></div>
    </div>
    <div class="cr-links">
      <a class="ver" href="{feed}" target="_blank" rel="noopener">Abrir arte 1:1</a>
      {f'<a class="ver" href="{story}" target="_blank" rel="noopener">Abrir story 9:16</a>' if story else ''}
      <details class="cr-copy"><summary>Ver a copy completa</summary><pre>{html.escape(r['body'])}</pre></details>
    </div>
  </div>
</article>''')
    return '\n'.join(out), rows

def totais(curso):
    rows = [v for v in D[curso].values() if 'spend' in v]
    s = sum(r['spend'] for r in rows); c = sum(r['conv'] for r in rows)
    return s, c, (s / c if c else 0), len(rows)

esp_cards, esp_rows = cards('ESPEC')
ime_cards, ime_rows = cards('IMERSAO')
es, ec, ecpc, en = totais('ESPEC')
ims, imc, imcpc, imn = totais('IMERSAO')

CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'estilo.css')).read()

HTML = f'''<title>Criativos dos presenciais HOF</title>
<style>{CSS}</style>
<div class="wrap">
<header class="topo">
  <div><p class="olho">Delva Education · Agosto de 2026</p>
  <h1>Os criativos que<br>puxaram conversa</h1>
  <p class="sub-t">Primeira semana no ar dos dois cursos presenciais. Cada peça abaixo tem a arte, a chamada, a copy e o que ela entregou — na ordem do que custou mais barato para gerar uma conversa no WhatsApp.</p></div>
  <div class="selo"><b>{en + imn}</b>criativos com entrega<br>{brl(es + ims)} investidos<br>{ec + imc:.0f} conversas iniciadas</div>
</header>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Leitura rápida</p><h2>O que essa semana disse</h2></div></div>
  <div class="destaques">
    <div class="dcard"><span class="d-l">Especialização · melhor peça</span><b>{brl(esp_rows[0]['spend']/esp_rows[0]['conv'])}</b><span class="d-d">“{html.escape(esp_rows[0]['title'])}” · {esp_rows[0]['conv']:.0f} conversas</span></div>
    <div class="dcard"><span class="d-l">Imersão Iniciantes · melhor peça</span><b>{brl(ime_rows[0]['spend']/ime_rows[0]['conv'])}</b><span class="d-d">“{html.escape(ime_rows[0]['title'])}” · {ime_rows[0]['conv']:.0f} conversas</span></div>
    <div class="dcard"><span class="d-l">Média Especialização</span><b>{brl(ecpc)}</b><span class="d-d">{ec:.0f} conversas · {brl(es)} · público quente</span></div>
    <div class="dcard"><span class="d-l">Média Imersão</span><b>{brl(imcpc)}</b><span class="d-d">{imc:.0f} conversas · {brl(ims)} · público frio</span></div>
  </div>
  <div class="texto">
    <p>São duas ofertas muito diferentes rodando ao mesmo tempo. A <b>Especialização</b> fala com quem já acompanha o Dr. Marcelo Germani — público quente, região de Rio Preto — e por isso entrega mais caro por mil impressões, mas converte melhor. A <b>Imersão para Iniciantes</b> fala com quem nunca ouviu falar do curso: público frio, nove cidades, mídia barata e conversa mais cara.</p>
    <p>Com uma semana no ar e volumes ainda pequenos, o que vale é a <b>direção</b> — qual tipo de chamada puxa conversa e qual não puxa. É isso que está mapeado abaixo, peça por peça.</p>
  </div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Dr. Marcelo Germani · público quente · 25 a 31 de agosto</p><h2>Especialização em HOF de Alta Performance</h2></div>
  <div class="curso-tot"><span class="tot-l">Investido</span><span class="tot-v">{brl(es)}</span></div></div>
  <p class="nota-secao">{en} artes no ar, uma por conjunto, com o mesmo público: quem já interagiu com o perfil do Dr. Germani nos últimos 180 a 365 dias. Como o público é pequeno, a mesma pessoa viu o anúncio em média 6 vezes na semana — é o limite natural dessa audiência.</p>
  <div class="grade">{esp_cards}</div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Prof. Júlia Corazzina · público frio · 26 a 31 de agosto</p><h2>3ª Imersão HOF para Iniciantes</h2></div>
  <div class="curso-tot"><span class="tot-l">Investido</span><span class="tot-v">{brl(ims)}</span></div></div>
  <p class="nota-secao">{imn} artes com entrega, em dois públicos frios: <b>Odonto</b> (formação e cargo em Odontologia, com a chamada “Dentista recém-formada:” na abertura) e <b>Mix saúde</b> (odonto + biomedicina, fisioterapia, farmácia, enfermagem, sem chamada de profissão).</p>
  <div class="grade">{ime_cards}</div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">A resposta curta</p><h2>Qual é a chamada que funciona</h2></div></div>
  <div class="eixos">
    <div class="eixo bom">
      <h3>Puxou conversa</h3>
      <ul>
        <li><b>Medo do erro clínico.</b> “O erro mais caro em HOF não é o que dá errado na hora. É o que aparece depois.” — a peça de melhor volume da Especialização. Fala com quem já aplica e tem medo de assinar um resultado ruim.</li>
        <li><b>Defasagem técnica.</b> “A HOF evoluiu muito. A pergunta é se a sua formação evoluiu junto.” — melhor CTR da conta (1,48%). Cutuca sem ofender.</li>
        <li><b>Autoridade exclusiva.</b> “Existe um único Doutor em HOF no Brasil. E é com ele que você vai estudar.” — funciona porque é um fato verificável, não um adjetivo.</li>
        <li><b>Segurança antes da técnica</b> (Iniciantes). “Antes da seringa vem a decisão” e “construir uma base que ainda vai estar de pé daqui a cinco anos” — as duas melhores do frio.</li>
        <li><b>Chamar a profissão no primeiro parágrafo.</b> “Dentista recém-formada:” fez o público Odonto entregar a até um terço do custo de mídia do público misto.</li>
      </ul>
    </div>
    <div class="eixo ruim">
      <h3>Não puxou</h3>
      <ul>
        <li><b>Argumento de dinheiro.</b> “Especialização não é custo, é o que separa quem cobra por procedimento de quem cobra por resultado” — zero conversa. Retorno financeiro não é o gatilho desse público.</li>
        <li><b>Cobrança de estagnação.</b> “Faz quanto tempo que você não aprende uma técnica nova?” — zero conversa. Soa como julgamento.</li>
        <li><b>Formato e duração.</b> “18 meses de acompanhamento”, “curso de fim de semana não forma especialista” — informação de grade, não dor. Zero conversa.</li>
        <li><b>Promessa genérica.</b> “Do básico ao avançado” — o CTR mais baixo de todos (0,31%).</li>
        <li><b>Anúncio sem chamada de profissão no frio.</b> As mesmas copies, sem o “Dentista recém-formada:”, custaram de duas a três vezes mais caro por mil impressões.</li>
      </ul>
    </div>
  </div>
  <div class="texto">
    <p class="regra">A regra que sai daí: <b>o gancho vencedor é sempre uma consequência clínica</b> — o que acontece com o paciente, com o resultado e com a reputação de quem aplica. Grade de curso, tempo de formação e preço não abrem conversa; risco, atualização e autoridade abrem.</p>
  </div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Próximo lote</p><h2>O que vamos testar em cima do que funcionou</h2></div></div>
  <div class="testes">
    <div class="tcard"><span class="t-n">01</span><h4>Caso de intercorrência</h4><p>Continuação direta da peça de melhor volume: o resultado que migrou, a assimetria que apareceu no terceiro mês, o paciente que sumiu. Termina em “o que você faria?”.</p><span class="t-eixo">Eixo: medo do erro clínico</span></div>
    <div class="tcard"><span class="t-n">02</span><h4>Antes e depois de planejamento</h4><p>Não o rosto do paciente — o plano. Mostrar como um especialista avalia o mesmo rosto que o generalista só “preenche”.</p><span class="t-eixo">Eixo: domínio técnico</span></div>
    <div class="tcard"><span class="t-n">03</span><h4>O que mudou em cinco anos</h4><p>Lista curta do que virou obsoleto na HOF. Sequência natural da peça de melhor CTR.</p><span class="t-eixo">Eixo: defasagem técnica</span></div>
    <div class="tcard"><span class="t-n">04</span><h4>Credencial em números</h4><p>Doutorado, publicações, palestras internacionais, alunos formados — a autoridade dita em dados, não em adjetivo.</p><span class="t-eixo">Eixo: autoridade exclusiva</span></div>
    <div class="tcard"><span class="t-n">05</span><h4>Vídeo do professor falando</h4><p>Toda a conta é imagem estática hoje. Trinta segundos do Dr. Germani com o mesmo gancho da peça campeã é o teste de formato mais óbvio que ainda não fizemos.</p><span class="t-eixo">Formato novo</span></div>
    <div class="tcard"><span class="t-n">06</span><h4>Depoimento de aluno em atendimento</h4><p>Prova social vinda de quem já fez, falando de segurança clínica — não de “curso incrível”.</p><span class="t-eixo">Eixo: segurança</span></div>
    <div class="tcard"><span class="t-n">07</span><h4>“A consulta trava antes da agulha”</h4><p>Versão para iniciantes do gancho de decisão clínica que foi o melhor do público frio.</p><span class="t-eixo">Iniciantes</span></div>
    <div class="tcard"><span class="t-n">08</span><h4>Chamada por profissão, uma a uma</h4><p>“Dentista recém-formada”, “Biomédica esteta”, “Fisioterapeuta dermatofuncional” — uma peça para cada, em vez de um anúncio genérico para o público misto.</p><span class="t-eixo">Iniciantes</span></div>
    <div class="tcard"><span class="t-n">09</span><h4>Bastidor do hands-on</h4><p>Foto real da turma anterior aplicando, com supervisão. Sustenta a promessa de “você não vai só observar”.</p><span class="t-eixo">Prova</span></div>
    <div class="tcard"><span class="t-n">10</span><h4>Contagem de vagas</h4><p>Urgência real, com número de vagas restantes, para entrar só na reta final — depois que os ganchos de dor já aqueceram o público.</p><span class="t-eixo">Fechamento</span></div>
  </div>
</section>

<section class="notas">
  <h3>Como ler estes números</h3>
  <ul>
    <li><b>Conversa iniciada</b> é a pessoa que abriu o WhatsApp e enviou a primeira mensagem. É a métrica que o Meta otimiza nas duas campanhas.</li>
    <li>O período é curto — <b>de 5 a 7 dias por campanha</b> — e o volume por peça ainda é baixo. Serve para escolher direção de criativo, não para cravar um vencedor definitivo.</li>
    <li>Na Especialização existe uma <b>regra automática</b>: conjunto que passa de R$ 35 sem nenhuma conversa é pausado sozinho. É por isso que quatro peças aparecem com investimento baixo e zero conversa — elas foram cortadas cedo, de propósito.</li>
    <li>Cada anúncio roda com <b>duas artes</b>: a versão 1:1 no feed e a 9:16 em stories e reels. Os dois links estão em cada peça.</li>
    <li>Fonte: Meta Ads, nível de anúncio, período total de veiculação de cada campanha. Fechamento em 31 de agosto de 2026.</li>
  </ul>
</section>
</div>'''

open(os.path.join(BASE, 'index.html'), 'w').write(HTML)
print('ok', os.path.join(BASE, 'index.html'), len(HTML))
