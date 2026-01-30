// --- user.js ---
// This script runs for the USER dashboard.
// It displays live charts of crowd data (ages, gender, etc.)

const socket = io();
let mallState = {};

// When connected, log confirmation
socket.on('connect', () => {
    console.log('User connected to socket.');
});

// When full initial state is received from backend
socket.on('full_state', (data) => {
    mallState = data.mall || {};
    renderCharts();
});

// When mall update happens (after admin uploads video)
socket.on('mall_update', (data) => {
    mallState = data || {};
    renderCharts();
});

// Function to render charts
function renderCharts() {
    if (!mallState || !mallState.ages) {
        console.log("No age data yet.");
        return;
    }

    // ---- Render Age Pie Chart ----
    const ctx = document.getElementById('ageChart').getContext('2d');
    if (window.ageChartObj) {
        window.ageChartObj.destroy();
    }

    window.ageChartObj = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(mallState.ages),
            datasets: [{
                data: Object.values(mallState.ages),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'Crowd Age Distribution' }
            }
        }
    });

    // ---- Optional: Gender Pie Chart ----
    if (mallState.genders) {
        const gctx = document.getElementById('genderChart').getContext('2d');
        if (window.genderChartObj) {
            window.genderChartObj.destroy();
        }

        window.genderChartObj = new Chart(gctx, {
            type: 'pie',
            data: {
                labels: Object.keys(mallState.genders),
                datasets: [{
                    data: Object.values(mallState.genders),
                    backgroundColor: ['#36A2EB', '#FF6384']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'Gender Distribution' }
                }
            }
        });
    }
}