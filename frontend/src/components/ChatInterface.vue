<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>Terminal de Decisión Operativa</h2>
      <div :class="['status-indicator', connectionStatus]">
        {{ connectionStatusText }}
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-content">
          <div class="message-author">{{ msg.role === 'user' ? 'Operario' : 'Agente Cognitivo PTAR' }}</div>
          <p class="text-body">{{ msg.content }}</p>
          
          <div v-if="msg.role === 'assistant' && msg.metadata" class="metadata-box">
            <span class="strategy-badge" :class="msg.metadata.routing_strategy === 'Manuales y Normativa' ? 'RAG' : 'CBR'">
              Fuente: {{ msg.metadata.routing_strategy }}
            </span>
            <details v-if="msg.metadata.sources && msg.metadata.sources.length > 0">
              <summary>Archivos Recuperados ({{ msg.metadata.sources.length }})</summary>
              <ul class="sources-list">
                <li v-for="(source, idx) in msg.metadata.sources" :key="idx">
                  <strong>Origen:</strong> {{ source.author }} <br>
                  <strong>Nivel de coincidencia:</strong> {{(source.similarity * 100).toFixed(2)}}%
                </li>
              </ul>
            </details>
          </div>
        </div>
      </div>
      <div v-if="isTyping" class="message assistant typing-indicator">
        Generando respuesta del modelo local...
      </div>
    </div>

    <div class="chat-input-area">
      <textarea 
        v-model="currentInput" 
        @keydown.enter.prevent="sendMessage"
        placeholder="Describa el problema operativo (ej. El lodo en el sedimentador primario presenta burbujas)..."
        :disabled="connectionStatus !== 'connected' || isTyping"
        rows="3"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="!currentInput.trim() || connectionStatus !== 'connected' || isTyping"
        class="btn-send"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';

const props = defineProps({
  equalizerSettings: {
    type: Object,
    required: true
  }
});

const messages = ref([]);
const currentInput = ref('');
const connectionStatus = ref('disconnected'); // 'disconnected', 'connected', 'error'
const connectionStatusText = ref('Desconectado');
const isTyping = ref(false);
const messagesContainer = ref(null);

let socket = null;
let currentAssistantMessageIndex = -1;

const connectWebSocket = () => {
  connectionStatus.value = 'connecting';
  connectionStatusText.value = 'Conectando al Motor Local...';
  
  socket = new WebSocket('ws://localhost:8055/ws/v1/stream');

  socket.onopen = () => {
    connectionStatus.value = 'connected';
    connectionStatusText.value = 'Conexión Segura Establecida';
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // CORRECCIÓN: Verifica el tipo exacto enviado por el backend
    if (data.type === 'error') {
      messages.value.push({ role: 'assistant', content: `[Error del Servidor]: ${data.content}` });
      isTyping.value = false;
      scrollToBottom();
      return;
    }

    if (data.type === 'metadata') {
      messages.value.push({
        role: 'assistant',
        content: '',
        metadata: {
          routing_strategy: data.strategy,
          sources: data.sources_used
        }
      });
      currentAssistantMessageIndex = messages.value.length - 1;
      isTyping.value = false; 
    } 
    else if (data.type === 'token') {
      if (currentAssistantMessageIndex !== -1) {
        messages.value[currentAssistantMessageIndex].content += data.content;
      }
    } 
    else if (data.type === 'end_of_stream') {
      currentAssistantMessageIndex = -1;
      scrollToBottom();
    }
  };

  socket.onclose = () => {
    connectionStatus.value = 'disconnected';
    connectionStatusText.value = 'Conexión Perdida. Reconectando...';
    setTimeout(connectWebSocket, 5000); 
  };

  socket.onerror = (error) => {
    connectionStatus.value = 'error';
    connectionStatusText.value = 'Fallo de Red';
  };
};

const sendMessage = () => {
  if (!currentInput.value.trim() || connectionStatus.value !== 'connected') return;

  const query = currentInput.value.trim();
  
  messages.value.push({ role: 'user', content: query });
  currentInput.value = '';
  isTyping.value = true;
  scrollToBottom();

  const payload = {
    message: query,
    profile: props.equalizerSettings.userProfile,
    threshold: props.equalizerSettings.similarityThreshold
  };

  socket.send(JSON.stringify(payload));
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

watch(messages, () => {
  if (currentAssistantMessageIndex !== -1) {
    scrollToBottom();
  }
}, { deep: true });

onMounted(() => {
  connectWebSocket();
});

onBeforeUnmount(() => {
  if (socket) {
    socket.close();
  }
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chat-header {
  padding: 16px 20px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  font-size: 1.2rem;
}

.status-indicator {
  font-size: 0.8rem;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.status-indicator.connected { background-color: #27ae60; color: white; }
.status-indicator.disconnected { background-color: #f39c12; color: white; }
.status-indicator.error { background-color: #e74c3c; color: white; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f9fbfd;
}

.message {
  margin-bottom: 20px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.message.user .message-content {
  background-color: #3498db;
  color: white;
  border-bottom-right-radius: 0;
}

.message.assistant .message-content {
  background-color: #ffffff;
  color: #333;
  border: 1px solid #e0e6ed;
  border-bottom-left-radius: 0;
}

.message-author {
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 5px;
  text-transform: uppercase;
  opacity: 0.8;
}

.text-body {
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.typing-indicator {
  font-style: italic;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.metadata-box {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #bdc3c7;
}

.strategy-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
  margin-bottom: 8px;
}

.strategy-badge.CBR { background-color: #8e44ad; color: white; }
.strategy-badge.RAG { background-color: #2980b9; color: white; }

details summary {
  font-size: 0.85rem;
  color: #34495e;
  cursor: pointer;
  font-weight: 600;
}

.sources-list {
  margin-top: 8px;
  padding-left: 20px;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.sources-list li {
  margin-bottom: 4px;
}

.chat-input-area {
  padding: 15px;
  background-color: #ffffff;
  border-top: 1px solid #e0e6ed;
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #bdc3c7;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
}

textarea:focus {
  outline: none;
  border-color: #3498db;
}

.btn-send {
  background-color: #2ecc71;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.btn-send:hover:not(:disabled) {
  background-color: #27ae60;
}

.btn-send:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}
</style>