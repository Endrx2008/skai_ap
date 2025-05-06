document.addEventListener('DOMContentLoaded', function () {
  const chat = document.getElementById('chat');
  const input = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const clearText = document.getElementById('clearText');

  let firstMessageSent = false;
  let helloMessageElem = null;

  function appendMessage(text, sender) {
    const messageElem = document.createElement('div');
    messageElem.classList.add('message', sender);

    // Extract label and message text
    let labelText = '';
    let messageText = text;
    if (text.startsWith('User: ')) {
      labelText = 'User:';
      messageText = text.substring(6);
    } else if (text.startsWith('Skai: ')) {
      labelText = 'Skai:';
      messageText = text.substring(6);
    }

    // Create label span
    const labelSpan = document.createElement('span');
    labelSpan.classList.add('label');
    labelSpan.textContent = labelText + ' ';

    // Create message text span
    const messageSpan = document.createElement('span');
    messageSpan.classList.add('text');
    messageSpan.textContent = messageText;

    // Append spans to message element
    messageElem.appendChild(labelSpan);
    messageElem.appendChild(messageSpan);

    chat.appendChild(messageElem);
    chat.scrollTop = chat.scrollHeight;
    return messageElem;
  }

  function showHelloMessage() {
    helloMessageElem = appendMessage('Say hello to skai', 'bot');
    helloMessageElem.classList.add('hello-message');
  }

  // Show "hello" message initially
  showHelloMessage();

  sendButton.addEventListener('click', () => {
    const userMessage = input.value.trim();
    if (!userMessage) return;

    // Remove "hello" message after first user message
    if (!firstMessageSent) {
      if (helloMessageElem && helloMessageElem.parentNode) {
        helloMessageElem.parentNode.removeChild(helloMessageElem);
      }
      firstMessageSent = true;
    }

    appendMessage('User: ' + userMessage, 'user');
    input.value = '';

    // Simple bot response for demonstration
    appendMessage('Skai: ' + userMessage, 'bot');
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendButton.click();
    }
  });

  clearText.addEventListener('click', () => {
    // Clear all messages
    chat.innerHTML = '';
    // Reset state
    firstMessageSent = false;
    // Show hello message again
    showHelloMessage();
  });
});
