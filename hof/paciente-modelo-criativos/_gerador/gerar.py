#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatório de criativos — HOF Paciente Modelo (Rio Preto). Lote novo de agosto/26 + 10 propostas."""
import json, os, html, re

G = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(G)
REPO = os.path.abspath(os.path.join(BASE, '..', '..'))
D = json.load(open(os.path.join(G, 'dados.json')))
PROP = json.load(open(os.path.join(G, 'propostas.json')))
COPY_MD = open(os.path.join(G, 'copy_atual.md')).read()

def brl(v):
    return ('R$ ' + f'{v:,.2f}').replace(',', 'X').replace('.', ',').replace('X', '.')

# ---- copies das peças que rodaram, extraídas do COPY.md
copies = {}
for m in re.finditer(r'^## (\d+) · (\w+).*?\*\*Texto principal:\*\*\n(.*?)\n\*\*Título:\*\* (.*?)\n', COPY_MD, re.S | re.M):
    num, nome, corpo, titulo = m.groups()
    corpo = '\n'.join(l[2:] if l.startswith('> ') else ('' if l.strip() == '>' else l) for l in corpo.strip().split('\n'))
    copies[nome] = dict(num=num, titulo=titulo.strip(), corpo=corpo.strip())

ORDEM = ['CARTAZ_EDITAL', 'CHECKLIST', 'PERFIL_MANDIBULA', 'LINHA_DO_TEMPO', 'AB_HOMEM', 'FAIXA_45MAIS', 'HERO_MULHER_JOVEM']
ARQ = {'CARTAZ_EDITAL': '08_CARTAZ_EDITAL', 'CHECKLIST': '09_CHECKLIST', 'PERFIL_MANDIBULA': '07_PERFIL_MANDIBULA',
       'LINHA_DO_TEMPO': '05_LINHA_DO_TEMPO', 'AB_HOMEM': '01_AB_HOMEM', 'FAIXA_45MAIS': '03_FAIXA_45MAIS',
       'HERO_MULHER_JOVEM': '02_HERO_MULHER_JOVEM'}
RESSALVA = {
  'AB_HOMEM': 'Peça masculina entregue só para mulheres — o conjunto foi montado com gênero feminino. Teste inválido.',
  'FAIXA_45MAIS': 'Recebeu R$ 6,45 de mídia num público de 25 a 65 anos. Não chegou a ter teste.',
  'HERO_MULHER_JOVEM': 'Recebeu R$ 6,63 e 81 impressões. Não chegou a ter teste.',
}

def peca(k):
    d = D['novos'][k]; c = copies.get(k, {})
    feed = f'/criativos/hof-paciente-modelo/FEED_{ARQ[k]}.jpg'
    story = f'/criativos/hof-paciente-modelo/STORY_{ARQ[k]}.jpg'
    cpc = d['spend'] / d['conv'] if d['conv'] else None
    venceu = d['conv'] >= 5
    medalha = 'Campeã do lote' if venceu else ('Sem teste justo' if k in RESSALVA else 'Pouca conversa')
    resp = f"{d['rep']:.0f} de {d['conv']:.0f} responderam" if d['conv'] else '—'
    return f'''
<article class="cr{' vence' if venceu else ''}{' zero' if not d['conv'] else ''}">
  <a class="cr-img" href="{feed}" target="_blank" rel="noopener"><img src="{feed}" alt="{k}" loading="lazy" width="900" height="900"></a>
  <div class="cr-corpo">
    <div class="cr-top"><span class="cr-id">{k.replace('_',' ').title()}</span><span class="pin">{medalha}</span></div>
    <h4>{html.escape(c.get('titulo',''))}</h4>
    <p class="cr-gancho">{html.escape(c.get('corpo','').split(chr(10))[0])}</p>
    <div class="cr-num">
      <div><b>{brl(cpc) if cpc else '—'}</b><span>por conversa</span></div>
      <div><b>{d['conv']:.0f}</b><span>conversas</span></div>
      <div><b>{brl(d['spend'])}</b><span>investido</span></div>
      <div><b>{d['ctr']:.2f}%</b><span>CTR</span></div>
      <div><b>{resp}</b><span>continuaram a conversa</span></div>
    </div>
    {f'<p class="ressalva">{RESSALVA[k]}</p>' if k in RESSALVA else ''}
    <div class="cr-links">
      <a class="ver" href="{feed}" target="_blank" rel="noopener">Abrir arte 1:1</a>
      <a class="ver" href="{story}" target="_blank" rel="noopener">Abrir story 9:16</a>
      <details class="cr-copy"><summary>Ver a copy completa</summary><pre>{html.escape(c.get('corpo',''))}</pre></details>
    </div>
  </div>
</article>'''

pecas = '\n'.join(peca(k) for k in ORDEM)
tot_s = sum(d['spend'] for d in D['novos'].values())
tot_c = sum(d['conv'] for d in D['novos'].values())
ed = D['novos']['CARTAZ_EDITAL']; ch = D['novos']['CHECKLIST']
camp_s = ed['spend'] + ch['spend']; camp_c = ed['conv'] + ch['conv']
base = D['base']['AD_PACIENTE_PARCELAR']
ganho = (base['cpc'] - camp_s / camp_c) / base['cpc'] * 100

props = '\n'.join(f'''
<article class="prop">
  <a class="prop-img" href="/criativos/hof-paciente-modelo-set26/FEED_{p['arq']}.jpg" target="_blank" rel="noopener">
    <img src="/criativos/hof-paciente-modelo-set26/FEED_{p['arq']}.jpg" alt="{html.escape(p['nome'])}" loading="lazy" width="900" height="900">
  </a>
  <div class="prop-top"><span class="t-n">{p['n']}</span><span class="prop-pub">{html.escape(p['publico'])}</span></div>
  <h4>{html.escape(p['nome'])}</h4>
  <p class="prop-base">{html.escape(p['base'])}</p>
  <p class="prop-arte"><b>Arte:</b> {html.escape(p['arte'])}</p>
  <pre class="prop-copy">{html.escape(p['copy'])}</pre>
  <p class="prop-meta"><b>Título do anúncio:</b> {html.escape(p['titulo'])} · <b>Descrição:</b> {html.escape(p['desc'])}</p>
  <p class="prop-links"><a class="ver" href="/criativos/hof-paciente-modelo-set26/FEED_{p['arq']}.jpg" target="_blank" rel="noopener">Abrir arte 1:1</a> <a class="ver" href="/criativos/hof-paciente-modelo-set26/STORY_{p['arq']}.jpg" target="_blank" rel="noopener">Abrir story 9:16</a></p>
  <p class="prop-obs">{html.escape(p['obs'])}</p>
</article>''' for p in PROP)

CSS = open(os.path.join(G, 'estilo.css')).read() + '''
.ressalva{margin:0 0 12px;font-size:12.5px;color:var(--tijolo);border-left:2px solid color-mix(in srgb,var(--tijolo) 45%,transparent);padding-left:10px;line-height:1.45}
.props{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}
.prop{background:var(--card);border:1px solid var(--linha);border-radius:2px;padding:0 0 20px;box-shadow:var(--sombra);overflow:hidden}
.prop>*:not(.prop-img){margin-left:22px;margin-right:22px}
.prop-img{display:block;background:#0b0b0c;margin-bottom:16px}
.prop-img img{width:100%;height:auto;display:block}
.prop-links{margin:0 0 8px;display:flex;gap:14px;flex-wrap:wrap}
.prop-top{margin-top:16px;display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:6px}
.prop-pub{font-family:var(--mono);font-size:10px;color:var(--muted);text-align:right}
.prop h4{font-size:17px;margin-bottom:8px;line-height:1.25}
.prop-base{margin:0 0 10px;font-size:13px;color:var(--muted);line-height:1.5}
.prop-arte{margin:0 0 12px;font-size:12.5px;color:var(--muted);line-height:1.5}
.prop-arte b,.prop-meta b{color:var(--ink)}
.prop-copy{white-space:pre-wrap;font-family:var(--corpo);font-size:13px;color:var(--texto);line-height:1.55;
  background:color-mix(in srgb,var(--teal) 5%,transparent);border-left:2px solid color-mix(in srgb,var(--teal) 35%,transparent);padding:14px 16px;margin:0 0 12px}
.prop-meta{margin:0 0 8px;font-size:12px;color:var(--muted)}
.prop-obs{margin:0;font-size:12px;color:var(--gold);line-height:1.5}
@media (max-width:820px){.props{grid-template-columns:1fr}}
'''

HTML = f'''<title>Paciente modelo — criativos</title>
<style>{CSS}</style>
<div class="wrap">
<header class="topo">
  <div><p class="olho">HOF Paciente Modelo · São José do Rio Preto · Agosto de 2026</p>
  <h1>Sete peças novas<br>e o que elas ensinaram</h1>
  <p class="sub-t">Lote de criativos que entrou no ar em 27 de agosto, o resultado de cada um em cinco dias de veiculação e as dez próximas peças propostas — construídas em cima do que deu certo.</p></div>
  <div class="selo"><b>{brl(camp_s/camp_c)}</b>por conversa nas duas campeãs<br>contra {brl(base['cpc'])} do melhor anúncio antigo<br>{ganho:.0f}% mais barato</div>
</header>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Resumo</p><h2>O que aconteceu</h2></div>
  <div class="curso-tot"><span class="tot-l">Investido no lote novo</span><span class="tot-v">{brl(tot_s)}</span></div></div>
  <div class="destaques">
    <div class="dcard"><span class="d-l">Cartaz “Procura-se”</span><b>{brl(ed['spend']/ed['conv'])}</b><span class="d-d">{ed['conv']:.0f} conversas · CTR {ed['ctr']:.2f}%</span></div>
    <div class="dcard"><span class="d-l">Checklist “Você se encaixa?”</span><b>{brl(ch['spend']/ch['conv'])}</b><span class="d-d">{ch['conv']:.0f} conversas · CTR {ch['ctr']:.2f}%</span></div>
    <div class="dcard"><span class="d-l">Melhor anúncio antigo, no mesmo período</span><b>{brl(base['cpc'])}</b><span class="d-d">{base['conv']:.0f} conversas · {brl(base['spend'])}</span></div>
    <div class="dcard"><span class="d-l">Lote novo inteiro</span><b>{brl(tot_s/tot_c)}</b><span class="d-d">{tot_c:.0f} conversas · 7 peças</span></div>
  </div>
  <div class="texto">
    <p>O lote testou sete conceitos diferentes de uma vez. Dois deles bateram com folga tudo o que a conta tinha até agora: o <b>cartaz de convite</b> e o <b>checklist de autoqualificação</b> — os únicos que não usam “antes e depois” como argumento principal.</p>
    <p>E não é só preço. Das {ed['conv']:.0f} conversas abertas pelo cartaz, <b>{ed['rep']:.0f} viraram diálogo de verdade</b>, com resposta do outro lado. Historicamente o problema dessa conta é justamente o oposto: gente que abre a conversa e some.</p>
    <p class="regra">A leitura: <b>o paciente não responde ao resultado, responde ao convite.</b> Antes e depois mostra o que a clínica sabe fazer. Cartaz de seleção diz o que a pessoa precisa fazer agora — e é isso que abre conversa.</p>
  </div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">27 a 31 de agosto · campanha por pin de bairro</p><h2>As sete peças, uma a uma</h2></div></div>
  <p class="nota-secao">Na ordem de desempenho. Cada peça rodou em seu próprio conjunto, com arte 1:1 no feed e 9:16 em stories e reels, sempre com destino WhatsApp.</p>
  <div class="grade">{pecas}</div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Antes de tirar conclusão</p><h2>O que este teste ainda não respondeu</h2></div></div>
  <div class="eixos">
    <div class="eixo bom"><h3>Já dá para afirmar</h3><ul>
      <li><b>Formato de convite ganha de antes e depois</b> na abertura de conversa — as duas peças de seleção somam quase todo o resultado do lote.</li>
      <li><b>Autoqualificação melhora o CTR</b>: o checklist teve o maior índice de cliques de toda a conta no período.</li>
      <li><b>O cartaz traz gente que responde</b>, não só gente que clica. É a melhor proporção de conversa continuada que já medimos aqui.</li>
    </ul></div>
    <div class="eixo ruim"><h3>Ainda em aberto</h3><ul>
      <li><b>A peça masculina nunca foi testada.</b> Ela rodou dentro de um conjunto configurado só para mulheres. O conceito não foi reprovado — ele não foi julgado.</li>
      <li><b>As peças 45+ e mulher jovem receberam cerca de R$ 6 cada.</b> É pouco para qualquer leitura; ambas voltam no próximo lote com verba e faixa etária próprias.</li>
      <li><b>Antes e depois pode não estar errado, e sim mal endereçado.</b> A peça de perfil e mandíbula teve bom CTR e trouxe conversa — só que ao custo de {brl(D['novos']['PERFIL_MANDIBULA']['spend'])} por conversa. Vale rodar de novo dentro do formato de convite.</li>
    </ul></div>
  </div>
</section>

<section class="bloco">
  <div class="curso-cab"><div><p class="olho">Para aprovação</p><h2>As próximas peças</h2></div></div>
  <p class="nota-secao">Todas partem do mesmo mecanismo das duas campeãs: <b>convite claro, critério explícito e um passo único a dar</b>. Nenhuma traz data nem valor na arte ou na copy — preço e agenda continuam só na conversa do WhatsApp. <b>Já estão montadas</b>, em 1:1 para o feed e 9:16 para stories e reels: é só aprovar e subir.</p>
  <div class="props">{props}</div>
</section>

<section class="notas">
  <h3>Notas</h3>
  <ul>
    <li><b>Conversa iniciada</b> é a pessoa que abriu o WhatsApp e mandou a primeira mensagem. <b>Conversa continuada</b> é quando houve resposta depois disso — o indicador mais próximo de qualidade de contato que a plataforma entrega.</li>
    <li>Período: <b>27 a 31 de agosto de 2026</b>, cinco dias. A comparação com os anúncios antigos usa exatamente a mesma janela, para não misturar sazonalidade.</li>
    <li>As peças rodaram por bairro, com direcionamento por ponto no mapa em regiões de Rio Preto, e não por raio ao redor de shopping — mudança feita em agosto para melhorar a qualidade do contato.</li>
    <li>Uso de imagem dos pacientes das peças atuais: autorizado. As propostas que dependem de foto nova ou de depoimento só entram no ar com a mesma autorização assinada.</li>
    <li>Fonte: Meta Ads, nível de anúncio. Fechamento em 31 de agosto de 2026.</li>
  </ul>
</section>
</div>'''

open(os.path.join(BASE, 'index.html'), 'w').write(HTML)
print('ok', len(HTML))
