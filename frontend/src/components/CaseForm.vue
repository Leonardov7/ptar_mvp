<template>
  <div class="case-form-container">
    <div class="form-header">
      <h2>Registro de Bitácora Empírica</h2>
      <p>Documente las intervenciones operativas para alimentar el Razonamiento Basado en Casos (CBR).</p>
    </div>

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
        <label for="symptoms">Síntomas del Sistema (Vector de Estado):</label>
        <textarea 
          id="symptoms" 
          v-model="formData.symptoms" 
          rows="3" 
          placeholder="Describa la falla detalladamente (Ej: Aumento de turbidez, DBO5 elevada, pérdida de biomasa)." 
          required
          :disabled="isSubmitting"
        ></textarea>
      </div>

      <div class="form-group">
        <label for="action">Acción Heurística Ejecutada:</label>
        <textarea 
          id="action" 
          v-model="formData.action_taken" 
          rows="3" 
          placeholder="¿Qué acciones empíricas realizó? (Ej: Cierre de purga por 2 horas, incremento de aireación al 80%)." 
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
          placeholder="Describa el estado final del reactor (Ej: Estabilización del manto de lodos, corrección del parámetro)." 
          required
          :disabled="isSubmitting"
        ></textarea>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-submit" :disabled="isSubmitting">
          <span v-if="!isSubmitting">Indexar Caso en Base de Conocimiento</span>
          <span v-else>Vectorizando Caso...</span>
        </button>
      </div>

      <!-- Retroalimentación visual de la transacción -->
      <div v-if="notification.message" :class="['notification', notification.type]">
        {{ notification.message }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import api from '../services/api.js';

// Estado reactivo del formulario, enlazado bidireccionalmente con los inputs
const formData = reactive({
  author: '',
  symptoms: '',
  action_taken: '',
  result: ''
});

// Controladores de estado de la interfaz
const isSubmitting = ref(false);
const notification = reactive({
  message: '',
  type: '' // 'success' o 'error'
});

/**
 * Procesa el envío del formulario, bloquea interacciones repetidas
 * y gestiona la respuesta asíncrona del backend.
 */
const submitCase = async () => {
  isSubmitting.value = true;
  notification.message = '';
  
  try {
    const response = await api.submitEmpiricalCase({
      author: formData.author,
      symptoms: formData.symptoms,
      action_taken: formData.action_taken,
      result: formData.result
    });
    
    // Éxito: limpiar el formulario (excepto el autor) y notificar
    notification.type = 'success';
    notification.message = `Caso empírico indexado exitosamente (ID Vectorial: ${response.id}). Estructura CBR actualizada.`;
    
    formData.symptoms = '';
    formData.action_taken = '';
    formData.result = '';
    
    // Ocultar notificación de éxito tras 5 segundos
    setTimeout(() => {
      notification.message = '';
    }, 5000);
    
  } catch (error) {
    notification.type = 'error';
    const serverDetail = error.response?.data?.detail || error.message;
    notification.message = `Fallo crítico de indexación: ${serverDetail}`;
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.case-form-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.form-header h2 {
  margin-top: 0;
  color: #2c3e50;
  font-size: 1.5rem;
  border-bottom: 2px solid #3498db;
  padding-bottom: 8px;
}

.form-header p {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #34495e;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1rem;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
}

input[type="text"]:focus,
textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

input:disabled,
textarea:disabled {
  background-color: #ecf0f1;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-submit {
  background-color: #2980b9;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.btn-submit:hover:not(:disabled) {
  background-color: #3498db;
}

.btn-submit:disabled {
  background-color: #95a5a6;
  cursor: wait;
}

.notification {
  margin-top: 16px;
  padding: 12px;
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