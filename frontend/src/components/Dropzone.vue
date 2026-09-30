<template>
  <div class="dropzone-container">
    <div class="component-header">
      <h3>Ingesta Normativa</h3>
      <p>Procesamiento masivo de manuales técnicos y normativas.</p>
    </div>

    <div 
      class="drop-area" 
      :class="{ 'is-dragover': isDragging, 'is-processing': isProcessing }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <!-- Input oculto para múltiples archivos sueltos -->
      <input 
        type="file" 
        ref="fileInput" 
        accept="application/pdf" 
        multiple
        style="display: none;" 
        @change="handleFileSelect"
      />
      <!-- Input oculto para carpetas enteras -->
      <input 
        type="file" 
        ref="folderInput" 
        accept="application/pdf" 
        webkitdirectory 
        directory 
        multiple
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
        <p v-if="selectedFiles.length === 0">Arrastre PDFs aquí</p>
        <p v-else class="selected-file-name">{{ selectedFiles.length }} archivo(s) PDF detectado(s) en espera.</p>
        
        <div class="manual-triggers" v-if="selectedFiles.length === 0">
          <button class="btn-trigger" @click.stop="triggerFileInput">Seleccionar Archivos</button>
          <button class="btn-trigger" @click.stop="triggerFolderInput">Seleccionar Carpeta</button>
        </div>
      </div>

      <div v-else class="processing-content">
        <div class="spinner"></div>
        <p>Procesando lote de documentos...</p>
        <small>Por favor no cierre esta ventana.</small>
      </div>
    </div>

    <div class="action-bar" v-if="selectedFiles.length > 0 && !isProcessing">
      <button class="btn-process" @click="processFiles">Procesar {{ selectedFiles.length }} Documentos</button>
      <button class="btn-cancel" @click="clearSelection">Cancelar</button>
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
const folderInput = ref(null);
const selectedFiles = ref([]);

const triggerFileInput = () => {
  if (!isProcessing.value) fileInput.value.click();
};

const triggerFolderInput = () => {
  if (!isProcessing.value) folderInput.value.click();
};

const filterPdfs = (filesArray) => {
  const pdfs = [];
  for (let i = 0; i < filesArray.length; i++) {
    if (filesArray[i].type === 'application/pdf' || filesArray[i].name.toLowerCase().endsWith('.pdf')) {
      pdfs.push(filesArray[i]);
    }
  }
  return pdfs;
};

const handleDrop = (event) => {
  isDragging.value = false;
  const droppedPdfs = filterPdfs(event.dataTransfer.files);
  if (droppedPdfs.length > 0) {
    selectedFiles.value = droppedPdfs;
    resultMessage.value = '';
  } else {
    resultType.value = 'error';
    resultMessage.value = 'No se detectaron archivos PDF válidos en la selección.';
  }
};

const handleFileSelect = (event) => {
  const selected = filterPdfs(event.target.files);
  if (selected.length > 0) {
    selectedFiles.value = selected;
    resultMessage.value = '';
  }
  fileInput.value.value = '';
  folderInput.value.value = '';
};

const clearSelection = () => {
  selectedFiles.value = [];
  resultMessage.value = '';
};

const processFiles = async () => {
  if (selectedFiles.value.length === 0) return;

  isProcessing.value = true;
  resultMessage.value = '';

  try {
    const response = await api.uploadManual(selectedFiles.value);
    resultType.value = 'success';
    resultMessage.value = `Procesamiento exitoso. ${response.files_processed} documentos vectorizados en ${response.processing_time_seconds}s. Total fragmentos: ${response.chunks_created}.`;
    selectedFiles.value = [];
  } catch (error) {
    resultType.value = 'error';
    const serverDetail = error.response?.data?.detail || error.message;
    resultMessage.value = `Error crítico procesando el lote: ${serverDetail}`;
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
  padding: 20px 10px;
  text-align: center;
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
  margin: 10px 0 10px;
  color: #2c3e50;
  font-weight: 500;
}

.selected-file-name {
  color: #2980b9 !important;
  font-weight: bold !important;
}

.manual-triggers {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  margin-top: 15px;
}

.btn-trigger {
  background-color: #ecf0f1;
  border: 1px solid #bdc3c7;
  color: #34495e;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: bold;
  transition: background-color 0.2s;
  width: 80%;
}

.btn-trigger:hover {
  background-color: #d5dbdb;
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

.action-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 15px;
}

.btn-process {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-process:hover {
  background-color: #2980b9;
}

.btn-cancel {
  background-color: #ecf0f1;
  color: #7f8c8d;
  border: 1px solid #bdc3c7;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.btn-cancel:hover {
  background-color: #e0e6ed;
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