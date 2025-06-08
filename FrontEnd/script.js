const form = document.getElementById('form');
const surveyForm = document.getElementById('survey-form');
const planGrid = document.getElementById('plan-grid');
const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
let profile = null;
let plan = [];

form.addEventListener('submit', async e => {
  e.preventDefault();
  profile = {
    condition: document.getElementById('condition').value,
    dietaryPrefs: document.getElementById('dietaryPrefs').value,
    exercisePrefs: document.getElementById('exercisePrefs').value,
    busyDays: document.getElementById('busyDays').value
  };
  const res = await fetch('http://localhost:8000/api/plan', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify(profile)
  });
  const data = await res.json();
  plan = data.plan;
  renderPlan();
  surveyForm.classList.add('hidden');
  planGrid.classList.remove('hidden');
});

function renderPlan() {
  planGrid.innerHTML = '';
  plan.forEach(day => {
    const div = document.createElement('div');
    div.className = 'plan-day';
    div.innerHTML = `
      <h3>Day ${day.day}</h3>
      <p><strong>Meals:</strong></p>
      <ul>${day.meals.map(m => `<li>${m}</li>`).join('')}</ul>
      <p><strong>Suggestion:</strong> ${day.suggestions.join(', ')}</p>
      <p><strong>Ingredients:</strong> ${day.ingredients.join(', ')}</p>
      <p><strong>Activity:</strong> ${day.wellness.activity}</p>
      <p class="tip">${day.wellness.tip}</p>
    `;
    planGrid.appendChild(div);
  });
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  appendMessage('user', text);
  chatInput.value = '';
  const res = await fetch('http://localhost:8000/api/chat', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ profile, plan, message: text })
  });
  const { updatedPlan, reply } = await res.json();
  plan = updatedPlan;
  renderPlan();
  appendMessage('bot', reply);
}

function appendMessage(sender, text) {
  const msg = document.createElement('div');
  msg.className = `chat-message ${sender}`;
  const span = document.createElement('span');
  span.textContent = text;
  msg.appendChild(span);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', e => { if (e.key==='Enter') sendMessage(); });