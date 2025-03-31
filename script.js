const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');

function addMessage(content, isUser = false) {
  const messageDiv = document.createElement('div');
  const bubbleClass = isUser 
    ? 'bg-white border-2 border-gray-200 rounded-2xl' 
    : 'bg-gray-100 border-2 border-gray-300 rounded-2xl';
  messageDiv.className = `message ${bubbleClass} p-3 text-sm mb-3 max-w-[90%] ${isUser ? 'ml-auto' : 'mr-auto'}`;
  messageDiv.textContent = content;
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage(message, true);
  messageInput.value = '';
  
  try {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama2',
        prompt: message,
        stream: false
      })
    });

    const data = await response.json();
    addMessage(data.response);
  } catch (error) {
    addMessage('Error connecting to Ollama API. Make sure Kai is running.');
    console.error('API Error:', error);
  }
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Initial welcome message
addMessage('How can I help you?');
