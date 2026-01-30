const socket = io();
let state = {};
socket.on('connect', () => { console.log('socket connected'); });
socket.on('full_state', s => { state = s;
    render(); });
socket.on('parking_update', p => { state.parking = p;
    renderParking(); });
socket.on('mall_update', m => { state.mall = m;
    renderMall(); });

function render() {
    renderParking();
    renderMall();
}

function renderParking() {
    const container = document.getElementById('parking');
    container.innerHTML = '';
    for (const k in state.parking) {
        const div = document.createElement('div');
        div.className = 'slot ' + (state.parking[k] === 'free' ? 'free' : 'booked');
        div.innerHTML = `<strong>Slot ${k}</strong><br>${state.parking[k]}<br><button onclick="toggle(${k})">Toggle</button>`;
        container.appendChild(div);
    }
}

function renderMall() {
    const el = document.getElementById('mall_summary');
    el.innerHTML = JSON.stringify(state.mall, null, 2);
}

function toggle(k) {
    const newStatus = state.parking[k] === 'free' ? 'booked' : 'free';
    fetch('/api/toggle_parking', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot: k, status: newStatus }) });
}
document.getElementById('uploadForm').addEventListener('submit', async(e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await fetch('/api/upload_video', { method: 'POST', body: fd });
    const data = await res.json();
    document.getElementById('result').innerText = JSON.stringify(data, null, 2);
});