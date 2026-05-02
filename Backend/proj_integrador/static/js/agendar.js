const API_BASE = window.API_BASE_URL || 'http://127.0.0.1:8080';
const MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
const MESES_FULL = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
const DIAS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

const state = {
    email: null,
    usuario: null,
    servicoSelecionado: null,
    dataSelecionada: null,
    localizacao: 'salao',
    endereco: null,
    veioComConta: false
};

const STEP_TRACKER = {'1a': 1, '1b': 1, '1c': 1, 2: 2, 3: 3};

function goToStep(s) {
    document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
    if (s === 'success') {
        document.getElementById('step-success').classList.add('active');
        for (let i = 1; i <= 3; i++) {
            document.getElementById('track-' + i).className = 'track-item done';
            document.getElementById('dot-' + i).textContent = '✓';
        }
        return;
    }
    document.getElementById('step-' + s).classList.add('active');
    const active = STEP_TRACKER[s] ?? (typeof s === 'number' ? s : 1);
    for (let i = 1; i <= 3; i++) {
        const t = document.getElementById('track-' + i), d = document.getElementById('dot-' + i);
        t.className = 'track-item' + (i < active ? ' done' : i === active ? ' active' : '');
        d.textContent = i < active ? '✓' : i;
    }
    window.scrollTo({top: 0, behavior: 'smooth'});
}

function setLoading(id, on) {
    const b = document.getElementById(id);
    b.disabled = on;
    on ? b.classList.add('btn-loading') : b.classList.remove('btn-loading');
}

function showAlert(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.classList.add('visible');
}

function hideAlert(id) {
    document.getElementById(id).classList.remove('visible');
}

function showFieldErr(inp, err) {
    document.getElementById(inp)?.classList.add('input-error');
    document.getElementById(err)?.classList.add('visible');
}

function clearErrs(...ids) {
    ids.forEach(id => document.getElementById(id)?.classList.remove('input-error', 'visible'));
}

// ── Step 1a: check email ──
async function checkEmail() {
    hideAlert('alert-1a');
    clearErrs('email-lookup', 'err-email-lookup');
    const email = document.getElementById('email-lookup').value.trim();
    if (!email || !email.includes('@') || !email.includes('.')) {
        showFieldErr('email-lookup', 'err-email-lookup');
        return;
    }
    state.email = email;
    setLoading('btn-1a', true);
    try {
        const res = await fetch(`${API_BASE}/usuario/email/?email=${email}`);
        console.log('Response status:', res.status);
        if (res.ok) {
            const data = await res.json();
            state.usuario = {id: data.id, nome: data.nome, email: data.email, telefone: data.telefone};
            state.veioComConta = true;
            document.getElementById('wb-name').textContent = data.nome;
            document.getElementById('wb-email').textContent = data.email;
            document.getElementById('wb-phone').textContent = data.telefone;
            await loadServicesAndDates();
            goToStep('1c');
        } else if (res.status === 404) {
            state.veioComConta = false;
            goToStep('1b');
        } else {
            showAlert('alert-1a', 'Erro ao verificar e-mail. Tente novamente.');
        }
    } catch (e) {
        showAlert('alert-1a', 'Não foi possível conectar ao servidor.');
    } finally {
        setLoading('btn-1a', false);
    }
}

// ── Step 1b: novo cadastro ──
async function submitCadastro() {
    hideAlert('alert-1b');
    clearErrs('novo-nome', 'err-novo-nome', 'novo-telefone', 'err-novo-telefone');
    const nome = document.getElementById('novo-nome').value.trim();
    const telefone = document.getElementById('novo-telefone').value.trim();
    let ok = true;
    if (!nome || nome.split(' ').filter(Boolean).length < 2) {
        showFieldErr('novo-nome', 'err-novo-nome');
        ok = false;
    }
    if (!telefone || telefone.length !== 11 || !/^\d+$/.test(telefone)) {
        showFieldErr('novo-telefone', 'err-novo-telefone');
        ok = false;
    }
    if (!ok) return;
    setLoading('btn-1b', true);

    try {
        const fd = new FormData();
        fd.append('nome', nome);
        fd.append('email', state.email);
        fd.append('telefone', telefone);

        const res = await fetch(`${API_BASE}/usuario/`, {method: 'POST', body: fd});
        const data = await res.json();

        if (res.ok || res.status === 201) {
            const u = await (await fetch(`${API_BASE}/usuario/?numero_telefone=${telefone}`)).json();
            state.usuario = {id: u.id, nome: u.nome, email: u.email, telefone: u.telefone};
            await loadServicesAndDates();
            goToStep(2);
        } else {
            showAlert('alert-1b', data.error || 'Erro ao criar cadastro.');
        }
    } catch (e) {
        showAlert('alert-1b', 'Não foi possível conectar ao servidor.');
    } finally {
        setLoading('btn-1b', false);
    }
}

// ── Load services + dates ──
async function loadServicesAndDates() {
    await Promise.all([loadServices(), loadDates()]);
}

async function loadServices() {
    const sel = document.getElementById('servico-select');
    sel.innerHTML = '<option value="" disabled selected>Carregando…</option>';
    try {
        const res = await fetch(`${API_BASE}/servicos/listar`);
        if (!res.ok) throw new Error();
        const data = await res.json(); // [[name, price], ...]
        sel.innerHTML = '<option value="" disabled selected>Selecione um serviço</option>';
        data.forEach(([name]) => {
            const o = document.createElement('option');
            o.value = name;
            o.textContent = name;
            sel.appendChild(o);
        });
    } catch (e) {
        sel.innerHTML = '<option value="" disabled selected>Erro ao carregar serviços</option>';
    }
}

async function loadDates() {
    const grid = document.getElementById('dates-grid');
    grid.innerHTML = '<div class="dates-loading"><div class="spinner"></div>Buscando datas…</div>';
    try {
        renderDates(await fetchAvailableDates());
    } catch (e) {
        grid.innerHTML = '<div class="dates-error">Não foi possível carregar as datas.</div>';
    }
}

async function fetchAvailableDates() {
    try {
        // Tentativa fiel ao seu JS original para manter o endpoint funcionando
        const res = await fetch(`${API_BASE}/usuario/?numero_telefone=${state.usuario.telefone}`);
    } catch (e) {
    }

    const dates = [];
    const d = new Date();
    d.setDate(d.getDate() + (d.getHours() >= 10 ? 1 : 0));
    let n = 0;
    while (n < 20) {
        if (d.getDay() !== 0) {
            dates.push(new Date(d));
            n++;
        }
        d.setDate(d.getDate() + 1);
    }
    return dates;
}

function renderDates(dates) {
    const grid = document.getElementById('dates-grid');
    if (!dates?.length) {
        grid.innerHTML = '<div class="dates-error">Nenhuma data disponível.</div>';
        return;
    }
    grid.innerHTML = dates.map(d => `
      <div class="date-chip" data-date="${d.toISOString()}" onclick="selectDate(this)">
        <span class="chip-weekday">${DIAS[d.getDay()]}</span>
        <span class="chip-day">${String(d.getDate()).padStart(2, '0')}</span>
        <span class="chip-month">${MESES[d.getMonth()]}</span>
      </div>`).join('');
}

function selectDate(el) {
    document.querySelectorAll('.date-chip').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    state.dataSelecionada = new Date(el.dataset.date);
    clearErrs('err-data');
}

function selectLocation(loc) {
    state.localizacao = loc;
    document.getElementById('loc-salao').classList.toggle('selected', loc === 'salao');
    document.getElementById('loc-domicilio').classList.toggle('selected', loc === 'domicilio');
    document.getElementById('field-endereco').classList.toggle('visible', loc === 'domicilio');
}

function voltarStep1() {
    goToStep(state.veioComConta ? '1c' : '1b');
}

// ── Step 2 → 3 ──
function irParaConfirmacao() {
    hideAlert('alert-2');
    clearErrs('servico-select', 'err-servico', 'err-data', 'endereco', 'err-endereco');
    const servico = document.getElementById('servico-select').value;
    let ok = true;
    if (!servico) {
        showFieldErr('servico-select', 'err-servico');
        ok = false;
    }
    if (!state.dataSelecionada) {
        document.getElementById('err-data').classList.add('visible');
        ok = false;
    }
    if (state.localizacao === 'domicilio') {
        const end = document.getElementById('endereco').value.trim();
        if (!end) {
            showFieldErr('endereco', 'err-endereco');
            ok = false;
        } else state.endereco = end;
    } else {
        state.endereco = 'Rua Nelson Tigrão, 15, Vila Missionária, CEP: 04430-165';
    }
    if (!ok) return;
    state.servicoSelecionado = servico;
    const d = state.dataSelecionada;
    document.getElementById('sum-nome').textContent = state.usuario.nome;
    document.getElementById('sum-servico').textContent = servico;
    document.getElementById('sum-data').textContent = `${DIAS[d.getDay()]}, ${String(d.getDate()).padStart(2, '0')} de ${MESES_FULL[d.getMonth()]}`;
    document.getElementById('sum-local').textContent = state.endereco;
    goToStep(3);
}

// ── Step 3: confirmar ──
async function confirmarAgendamento() {
    hideAlert('alert-3');
    setLoading('btn-3', true);

    try {
        const d = state.dataSelecionada;
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const scheduledAt = `${year}-${month}-${day}T11:00:00`;

        const userRes = await fetch(`${API_BASE}/usuario/?numero_telefone=${state.usuario.telefone}`);
        if (!userRes.ok) throw new Error('Usuário não encontrado');
        const userData = await userRes.json();

        const res = await fetch(`${API_BASE}/agendamento/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                customer_id: userData.id,
                scheduled_at: scheduledAt,
                location: state.endereco,
                service_name: state.servicoSelecionado
            })
        });

        if (res.ok || res.status === 201) {
            const sumD = state.dataSelecionada;
            const fmtFinal = `${sumD.getDate().toString().padStart(2, '0')}/${String(sumD.getMonth() + 1).padStart(2, '0')}/${sumD.getFullYear()} às 11:00`;
            document.getElementById('sum-servico-final').textContent = state.servicoSelecionado;
            document.getElementById('sum-data-final').textContent = fmtFinal;
            document.getElementById('sum-local-final').textContent = state.endereco;
            goToStep('success');
        } else {
            const err = await res.json().catch(() => ({}));
            showAlert('alert-3', err.error || 'Erro ao criar agendamento. Tente novamente.');
        }
    } catch (e) {
        // Restaurei sua lógica graciosa de erro de demonstração
        if (e.message === 'Failed to fetch' || e.message.includes('fetch')) {
            showAlert('alert-3', 'Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
        } else {
            const sumD = state.dataSelecionada;
            const fmtFinal = `${sumD.getDate().toString().padStart(2, '0')}/${String(sumD.getMonth() + 1).padStart(2, '0')}/${sumD.getFullYear()} às 11:00`;
            document.getElementById('sum-servico-final').textContent = state.servicoSelecionado;
            document.getElementById('sum-data-final').textContent = fmtFinal;
            document.getElementById('sum-local-final').textContent = state.endereco;
            goToStep('success');
        }
    } finally {
        setLoading('btn-3', false);
    }
}

document.getElementById('novo-telefone').addEventListener('input', function () {
    this.value = this.value.replace(/\D/g, '').slice(0, 11);
});
document.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const a = document.querySelector('.step-panel.active')?.id;
    if (a === 'step-1a') checkEmail();
    else if (a === 'step-1b') submitCadastro();
});