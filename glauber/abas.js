/* ============================================================
   Barra de abas dos relatórios do Dr. Glauber.
   Publicada UMA vez em /glauber/abas.js e carregada por todas as
   páginas (resumo, perpetuo, lancamento, funil) — assim mexer na
   navegação é mexer num arquivo só, e cada dash segue sendo gerado
   pelo seu próprio workflow, no seu próprio horário.

   A barra lê a cor de fundo da página e se pinta sozinha: os dashes
   do Resumo/Biblioteca/Funil são escuros, o do Lançamento é claro —
   com paleta fixa ela sumia em cima do fundo branco.

   Uso na página:  <div id="ggd-abas"></div>
                   <script src="../abas.js"></script>   (raiz: "abas.js")
   ============================================================ */
(function () {
  var BASE = "/glauber/";
  var ABAS = [
    { id: "resumo",     rotulo: "Resumo",     nota: "visão geral",      href: BASE },
    { id: "perpetuo",   rotulo: "Biblioteca", nota: "perpétuo · R$ 97", href: BASE + "perpetuo/" },
    { id: "lancamento", rotulo: "Imersão",    nota: "lançamentos",      href: BASE + "lancamento/" },
    { id: "funil",      rotulo: "Funil 30d",  nota: "conta 01",         href: BASE + "funil/" }
  ];

  // qual aba está aberta: último segmento do caminho (raiz = resumo)
  var caminho = location.pathname.replace(/\/+$/, "");
  var ultimo = caminho.split("/").pop();
  var atual = "resumo";
  ABAS.forEach(function (a) { if (a.id === ultimo) atual = a.id; });

  // --- tema: claro ou escuro, conforme o fundo da própria página ---
  function luminancia(cor) {
    var m = (cor || "").match(/\d+(\.\d+)?/g);
    if (!m || m.length < 3) return 0;                 // sem cor legível: assume escuro
    return (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) / 255;
  }
  var fundo = getComputedStyle(document.body).backgroundColor;
  var claro = luminancia(fundo) > 0.6;

  var C = claro
    ? { linha:"#e2e6ec", aba:"#f4f6f9", abaHover:"#eaeef4", ativa:"#ffffff",
        texto:"#1c2330", apagado:"#68738a", nota:"#8b95a8", realce:"#2f6fd0" }
    : { linha:"#2a3441", aba:"#161b22", abaHover:"#1c2330", ativa:"#0d1117",
        texto:"#e6edf3", apagado:"#8b98a9", nota:"#6b7688", realce:"#4f9cff" };

  var css = document.createElement("style");
  css.textContent = [
    "#ggd-abas{margin:0 0 22px}",
    "#ggd-abas .marca{font-size:12px;color:" + C.apagado + ";letter-spacing:.6px;text-transform:uppercase;margin-bottom:10px}",
    "#ggd-abas .marca b{color:" + C.texto + ";font-weight:700;letter-spacing:-.2px;text-transform:none;font-size:14px}",
    "#ggd-abas nav{display:flex;flex-wrap:wrap;gap:6px;border-bottom:1px solid " + C.linha + "}",
    "#ggd-abas a{display:block;padding:9px 15px 10px;border:1px solid " + C.linha + ";border-bottom:none;",
    "  border-radius:9px 9px 0 0;background:" + C.aba + ";color:" + C.apagado + ";text-decoration:none;",
    "  font-size:13px;line-height:1.25;transition:background .12s,color .12s}",
    "#ggd-abas a:hover{background:" + C.abaHover + ";color:" + C.texto + "}",
    "#ggd-abas a .nota{display:block;font-size:10.5px;color:" + C.nota + ";margin-top:1px}",
    "#ggd-abas a.on{background:" + C.ativa + ";color:" + C.texto + ";font-weight:600;",
    "  box-shadow:inset 0 2px 0 " + C.realce + ";margin-bottom:-1px}",
    "#ggd-abas a.on .nota{color:" + C.apagado + "}",
    "@media(max-width:560px){#ggd-abas a{padding:8px 11px;font-size:12px}#ggd-abas a .nota{display:none}}"
  ].join("");
  document.head.appendChild(css);

  var alvo = document.getElementById("ggd-abas");
  if (!alvo) return;
  alvo.innerHTML =
    '<div class="marca"><b>Dr. Glauber Voltan</b> · relatórios GGD</div><nav>' +
    ABAS.map(function (a) {
      return '<a class="' + (a.id === atual ? "on" : "") + '" href="' + a.href + '">' +
             a.rotulo + '<span class="nota">' + a.nota + '</span></a>';
    }).join("") +
    '</nav>';
})();
