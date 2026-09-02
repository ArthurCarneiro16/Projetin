const API = "/api";
let usuarioAtual = null;

// ---------- Utilidades ----------
function $(sel) { return document.querySelector(sel); }
function $all(sel) { return document.querySelectorAll(sel); }

async function chamarApi(caminho, metodo = "GET", corpo = null) {
  const opcoes = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (corpo) opcoes.body = JSON.stringify(corpo);
  const resp = await fetch(API + caminho, opcoes);
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || "Erro inesperado");
  return dados;
}

// ---------- Abas (login/cadastro) ----------
$all("#tela-auth .aba").forEach((btn) => {
  btn.addEventListener("click", () => {
    $all("#tela-auth .aba").forEach((b) => b.classList.remove("ativa"));
    btn.classList.add("ativa");
    const aba = btn.dataset.aba;
    $("#form-login").classList.toggle("escondido", aba !== "login");
    $("#form-cadastro").classList.toggle("escondido", aba !== "cadastro");
  });
});

// ---------- Login ----------
$("#form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#login-erro").textContent = "";
  try {
    const dados = await chamarApi("/login", "POST", {
      nm_usuario: $("#login-nome").value,
      senha: $("#login-senha").value,
    });
    entrarNoApp(dados);
  } catch (err) {
    $("#login-erro").textContent = err.message;
  }
});

// ---------- Cadastro ----------
$("#form-cadastro").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#cad-erro").textContent = "";
  try {
    const dados = await chamarApi("/registrar", "POST", {
      nm_usuario: $("#cad-nome").value,
      senha: $("#cad-senha").value,
      altura: $("#cad-altura").value,
      peso: $("#cad-peso").value,
      idade: $("#cad-idade").value,
      sexo: $("#cad-sexo").value,
    });
    entrarNoApp(dados);
  } catch (err) {
    $("#cad-erro").textContent = err.message;
  }
});

function entrarNoApp(usuario) {
  usuarioAtual = usuario;
  $("#tela-auth").classList.add("escondido");
  $("#app").classList.remove("escondido");
  $("#nome-usuario-sidebar").textContent = usuario.nm_usuario;
  atualizarResumo();
}

$("#btn-sair").addEventListener("click", () => {
  usuarioAtual = null;
  $("#app").classList.add("escondido");
  $("#tela-auth").classList.remove("escondido");
  $("#form-login").reset();
});

// ---------- Navegação lateral ----------
$all(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    $all(".nav-item").forEach((i) => i.classList.remove("ativo"));
    item.classList.add("ativo");
    const secao = item.dataset.secao;
    $all(".secao").forEach((s) => s.classList.add("escondido"));
    $(`#secao-${secao}`).classList.remove("escondido");
    if (secao === "historico") carregarHistorico();
    if (secao === "resumo") atualizarResumo();
  });
});

// ---------- Resumo ----------
function atualizarResumo() {
  if (!usuarioAtual) return;
  $("#resumo-peso").textContent = `${usuarioAtual.peso} kg`;
  $("#resumo-altura").textContent = `${usuarioAtual.altura} m`;
  chamarApi(`/historico/${usuarioAtual.id_usuario}`)
    .then((lista) => {
      $("#resumo-ultimo-gasto").textContent = lista.length
        ? `${lista[0].gasto_calorico} kcal`
        : "—";
    })
    .catch(() => {});
}

// ---------- Registrar treino: abas cardio/musculação ----------
$all("#secao-registrar .aba").forEach((btn) => {
  btn.addEventListener("click", () => {
    $all("#secao-registrar .aba").forEach((b) => b.classList.remove("ativa"));
    btn.classList.add("ativa");
    const tipo = btn.dataset.tipo;
    $("#form-cardio").classList.toggle("escondido", tipo !== "cardio");
    $("#form-musculacao").classList.toggle("escondido", tipo !== "musculacao");
  });
});

$("#form-cardio").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fb = $("#cardio-feedback");
  fb.textContent = "";
  try {
    const dados = await chamarApi("/cardio", "POST", {
      id_usuario: usuarioAtual.id_usuario,
      nm_exercicio: $("#cardio-exercicio").value,
      duracao: $("#cardio-duracao").value,
      ritmo: $("#cardio-ritmo").value,
    });
    fb.style.color = "var(--blue)";
    fb.textContent = `${dados.nm_exercicio} registrado — ${dados.gasto_calorico} kcal`;
    e.target.reset();
  } catch (err) {
    fb.style.color = "var(--red)";
    fb.textContent = err.message;
  }
});

$("#form-musculacao").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fb = $("#musc-feedback");
  fb.textContent = "";
  try {
    const dados = await chamarApi("/musculacao", "POST", {
      id_usuario: usuarioAtual.id_usuario,
      exercicio: $("#musc-exercicio").value,
      peso_exerc: $("#musc-peso").value,
      repeticoes: $("#musc-repeticoes").value,
      series: $("#musc-series").value,
      tempo_treino: $("#musc-tempo").value,
    });
    fb.style.color = "var(--yellow)";
    fb.textContent = `${dados.exercicio} registrado — ${dados.gasto_calorico} kcal`;
    e.target.reset();
  } catch (err) {
    fb.style.color = "var(--red)";
    fb.textContent = err.message;
  }
});

// ---------- IMC ----------
$("#btn-calcular-imc").addEventListener("click", async () => {
  try {
    const dados = await chamarApi(`/imc/${usuarioAtual.id_usuario}`);
    $("#imc-valor").textContent = dados.imc;
    $("#imc-classificacao").textContent = dados.classificacao;
    $("#resultado-imc").classList.remove("escondido");
  } catch (err) {
    alert(err.message);
  }
});

// ---------- TMB ----------
$("#btn-calcular-tmb").addEventListener("click", async () => {
  const freq = $("#tmb-freq").value;
  if (freq === "") {
    alert("Informe quantas vezes por semana você treina.");
    return;
  }
  try {
    const dados = await chamarApi("/tmb", "POST", {
      id_usuario: usuarioAtual.id_usuario,
      exerc_p_semana: freq,
    });
    $("#tmb-gasto").textContent = `${dados.gasto_diario} kcal`;
    $("#resultado-tmb").classList.remove("escondido");
  } catch (err) {
    alert(err.message);
  }
});

// ---------- Histórico ----------
async function carregarHistorico() {
  const container = $("#lista-historico");
  container.innerHTML = `<p class="dica">Carregando...</p>`;
  try {
    const lista = await chamarApi(`/historico/${usuarioAtual.id_usuario}`);
    if (!lista.length) {
      container.innerHTML = `<p class="dica">Nenhum exercício registrado ainda.</p>`;
      return;
    }
    container.innerHTML = lista
      .map((item) => {
        const data = new Date(item.dia).toLocaleString("pt-BR", {
          day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
        });
        const meta =
          item.tipo === "musculacao"
            ? `${item.peso} kg · ${item.repeticoes} reps · ${item.series} séries`
            : `${item.tempo} · ritmo ${item.ritmo}`;
        return `
          <div class="item-historico">
            <div class="esquerda">
              <span class="tag-tipo ${item.tipo}">${item.tipo === "musculacao" ? "Musculação" : "Cardio"}</span>
              <span class="exercicio-nome">${item.exercicio}</span>
              <span class="exercicio-meta">${meta}</span>
              <span class="data">${data}</span>
            </div>
            <span class="gasto">${item.gasto_calorico} kcal</span>
          </div>`;
      })
      .join("");
  } catch (err) {
    container.innerHTML = `<p class="dica">Erro ao carregar histórico.</p>`;
  }
}
