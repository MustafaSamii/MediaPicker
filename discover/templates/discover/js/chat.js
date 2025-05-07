// static/discover/js/chat.js
const form   = document.getElementById("chat-form");
const input  = document.getElementById("chat-input");
const window = document.getElementById("chat-window");

form.addEventListener("submit", async e => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  // 1) show user bubble
  window.innerHTML += `<div class="user-bubble mb-2">${message}</div>`;
  input.value = "";

  // 2) send to /chat/
  const resp = await fetch("{% url 'discover:chat' %}", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken":  "{{ csrf_token }}",
    },
    body: JSON.stringify({ message }),
  });
  const { reply } = await resp.json();

  // 3) show bot bubble
  window.innerHTML += `<div class="bot-bubble mb-3">${reply}</div>`;
  window.scrollTop = window.scrollHeight;
});
