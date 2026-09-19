<template>
  <div class="case-form-wrapper">
    <div class="trigger-container">
      <div class="component-header">
        <h3>Bitácora Operativa</h3>
        <p>Almacenamiento de experiencia tácita en planta.</p>
      </div>
      <button class="btn-open-modal" @click="isModalOpen = true">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        Registrar Nueva Bitácora
      </button>
    </div>

    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Registro de Bitácora Operativa</h2>
          <button class="btn-close" @click="closeModal">&times;</button>
        </div>
        
        <p class="modal-description">Documente las fallas y soluciones aplicadas en la planta para conocimiento futuro.</p>

        <form @submit.prevent="submitCase" class="cbr-form">
          <div class="form-group">
            <label for="author">Identificador del Operario:</label>
            <input 
              type="text" 
              id="author" 
              v-model="formData.author" 
              placeholder="Ej: Ing. Juan Pérez / Turno Noche" 
              required 
              :disabled="isSubmitting"
            />
          </div>

          <div class="form-group">
            <label for="symptoms">Síntomas del Sistema:</label>
            <textarea 
              id="symptoms" 
              v-model="formData.symptoms" 
              rows="3" 
              placeholder="Describa la falla detalladamente (Ej: Aumento de turbidez, DBO5 elevada)." 
              required
              :disabled="isSubmitting"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="action">Acción Ejecutada:</label>
            <textarea 
              id="action" 
              v-model="formData.action_taken" 
              rows="3" 
              placeholder="¿Qué acciones realizó? (Ej: Cierre de purga por 2 horas)." 
              required
              :disabled="isSubmitting"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="result">Resultado Operativo:</label>
            <textarea 
              id="result" 
              v-model="formData.result" 
              rows="2" 
              placeholder="Describa el estado final del equipo tras la acción." 
              required
              :disabled="isSubmitting"
            ></textarea>
          </div>

          <div v-if="isSubmitting" class="progress-container">
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <span class="progress-text">Guardando información... {{ progress }}%</span>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="closeModal" :disabled="isSubmitting">Cancelar</button>
            <button type="submit" class="btn-submit" :disabled="isSubmitting">
              <span v-if="!isSubmitting">Guardar Registro</span>
              <span v-else>Procesando...</span>
            </button>
          </div>

          <div v-if="notification.message" :class="['notification', notification.type]">
            {{ notification.message }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import api from '../services/api.js';

const isModalOpen = ref(false);

const formData = reactive({
  author: '',
  symptoms: '',
  action_taken: '',
  result: ''
});

const isSubmitting = ref(false);
const progress = ref(0);
let progressInterval = null;

const notification = reactive({
  message: '',
  type: ''
});

const closeModal = () => {
  if (!isSubmitting.value) {
    isModalOpen.value = false;
    notification.message = '';
    progress.value = 0;
  }
};

const simulateProgress = () => {
  progress.value = 0;
  progressInterval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.floor(Math.random() * 15) + 5;
      if (progress.value > 90) progress.value = 90;
    }
  }, 400);
};

const stopProgress = () => {
  clearInterval(progressInterval);
  progress.value = 100;
};

const submitCase = async () => {
  isSubmitting.value = true;
  notification.message = '';
  simulateProgress();
  
  try {
    const response = await api.submitEmpiricalCase({
      author: formData.author,
      symptoms: formData.symptoms,
      action_taken: formData.action_taken,
      result: formData.result
    });
    
    stopProgress();
    notification.type = 'success';
    notification.message = `Registro guardado exitosamente (ID: ${response.id}).`;
    
    formData.symptoms = '';
    formData.action_taken = '';
    formData.result = '';
    
    setTimeout(() => {
      closeModal();
    }, 2000);
    
  } catch (error) {
    clearInterval(progressInterval);
    progress.value = 0;
    notification.type = 'error';
    const serverDetail = error.response?.data?.detail || error.message;
    notification.message = `Fallo al guardar: ${serverDetail}`;
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.trigger-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  padding: 20px;
  margin-bottom: 20px;
  border-left: 4px solid #2ecc71;
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

.btn-open-modal {
  width: 100%;
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 12px;
  font-size: 1rem;
  font-weight: bold;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: background-color 0.2s;
}

.btn-open-modal:hover {
  background-color: #27ae60;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #2ecc71;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.8rem;
  color: #7f8c8d;
  cursor: pointer;
}

.btn-close:hover {
  color: #e74c3c;
}

.modal-description {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  font-weight: 600;
  margin-bottom: 5px;
  color: #34495e;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.95rem;
  box-sizing: border-box;
}

input[type="text"]:focus,
textarea:focus {
  outline: none;
  border-color: #2ecc71;
  box-shadow: 0 0 0 2px rgba(46, 204, 113, 0.2);
}

.progress-container {
  margin-top: 15px;
  margin-bottom: 15px;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background-color: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-bar-fill {
  height: 100%;
  background-color: #2ecc71;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: #7f8c8d;
  font-weight: bold;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 25px;
}

.btn-submit {
  background-color: #2980b9;
  color: white;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
}

.btn-submit:disabled {
  background-color: #95a5a6;
  cursor: wait;
}

.btn-cancel {
  background-color: white;
  color: #7f8c8d;
  border: 1px solid #bdc3c7;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
}

.notification {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  font-weight: 500;
}

.notification.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>