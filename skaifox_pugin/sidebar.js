document.addEventListener('DOMContentLoaded', function () {
  const chat = document.getElementById('chat');
  const input = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');

  function appendMessage(text, sender) {
    const messageElem = document.createElement('div');
    messageElem.classList.add('message', sender);
    messageElem.textContent = text;
    chat.appendChild(messageElem);
    chat.scrollTop = chat.scrollHeight;
  }

  sendButton.addEventListener('click', () => {
    const userMessage = input.value.trim();
    if (!userMessage) return;
    appendMessage('User: ' + userMessage, 'user');
    input.value = '';

    // Simple bot response for demonstration
    setTimeout(() => {
      appendMessage('Skai: ' + userMessage, 'bot');
    }, 500);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendButton.click();
    }
  });
});
