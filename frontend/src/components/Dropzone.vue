<template>
  <div class="dropzone-container">
    <div class="component-header">
      <h3>Ingesta Normativa (RAG)</h3>
      <p>Vectorización de manuales técnicos y resoluciones gubernamentales.</p>
    </div>

    <div 
      class="drop-area" 
      :class="{ 'is-dragover': isDragging, 'is-processing': isProcessing }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input 
        type="file" 
        ref="fileInput" 
        accept="application/pdf" 
        style="display: none;" 
        @change="handleFileSelect"
      />
      
      <div v-if="!isProcessing" class="drop-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <line x1="9" y1="15" x2="15" y2="15"></line>
        </svg>
        <p>Arrastre un archivo PDF aquí, o haga clic para seleccionar.</p>
        <small>Solo se procesarán documentos teóricos para el fallback estructurado.</small>
      </div>

      <div v-else class="processing-content">
        <div class="spinner"></div>
        <p>Procesando con IBM Docling...</p>
        <small>Extrayendo tablas, ejecutando chunking y vectorizando texto.</small>
      </div>
    </div>

    <div v-if="resultMessage" :class="['result-message', resultType]">
      {{ resultMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../services/api.js';

const isDragging = ref(false);
const isProcessing = ref(false);
const resultMessage = ref('');
const resultType = ref('');
const fileInput = ref(null);

const triggerFileInput = () => {
  if (!isProcessing.value) {
    fileInput.value.click();
  }
};

const handleDrop = async (event) => {
  isDragging.value = false;
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    await processFile(files[0]);
  }
};

const handleFileSelect = async (event) => {
  const files = event.target.files;
  if (files.length > 0) {
    await processFile(files[0]);
  }
  // Limpiar el input para permitir subir el mismo archivo si hubo error
  fileInput.value.value = '';
};

const processFile = async (file) => {
  if (file.type !== 'application/pdf') {
    resultType.value = 'error';
    resultMessage.value = 'Formato inválido. Solo se admiten archivos PDF.';
    return;
  }

  isProcessing.value = true;
  resultMessage.value = '';

  try {
    const response = await api.uploadManual(file);
    resultType.value = 'success';
    resultMessage.value = `Documento vectorizado en ${response.processing_time_seconds}s. Chunks creados: ${response.chunks_created}.`;
  } catch (error) {
    resultType.value = 'error';
    const serverDetail = error.response?.data?.detail || error.message;
    resultMessage.value = `Error en el procesamiento: ${serverDetail}`;
  } finally {
    isProcessing.value = false;
  }
};
</script>

<style scoped>
.dropzone-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  padding: 20px;
  margin-bottom: 20px;
  border-left: 4px solid #3498db;
}

.component-header h3 {
  margin-top: 0;
  margin-bottom: 5px;
  color: #2c3e50;
  font-size: 1.1rem;
}

.component-header p {
  color: #7f8c8d;
  font-size: 0.85rem;
  margin-bottom: 15px;
  margin-top: 0;
}

.drop-area {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f9fbfd;
}

.drop-area:hover:not(.is-processing),
.drop-area.is-dragover {
  border-color: #3498db;
  background-color: #ebf5fb;
}

.drop-area.is-processing {
  cursor: wait;
  border-color: #f39c12;
  background-color: #fdfefe;
}

.drop-content p, .processing-content p {
  margin: 10px 0 5px;
  color: #2c3e50;
  font-weight: 500;
}

.drop-content small, .processing-content small {
  color: #7f8c8d;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #f39c12;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result-message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
}

.result-message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.result-message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>