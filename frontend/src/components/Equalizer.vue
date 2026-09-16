<template>
  <div class="equalizer-container">
    <div class="component-header">
      <h3>Ecualizador de Personalidad</h3>
      <p>Ajuste de parámetros de inferencia y umbral CBR.</p>
    </div>

    <div class="control-group">
      <label for="profile-select">Perfil Lingüístico del LLM:</label>
      <select id="profile-select" v-model="settings.userProfile" @change="emitUpdate">
        <option value="operator">Supervisor Operativo (Lenguaje directo y heurístico)</option>
        <option value="engineer">Ingeniero Ambiental (Rigor científico y termodinámico)</option>
      </select>
      <small class="helper-text">Modifica el System Prompt y la temperatura generativa.</small>
    </div>

    <div class="control-group">
      <label for="threshold-slider">Umbral de Similitud CBR ({{ settings.similarityThreshold }}):</label>
      <input 
        type="range" 
        id="threshold-slider" 
        min="0.5" 
        max="0.99" 
        step="0.01" 
        v-model.number="settings.similarityThreshold" 
        @input="emitUpdate"
      />
      <div class="slider-labels">
        <span>Más tolerante (RAG)</span>
        <span>Más estricto (CBR puro)</span>
      </div>
      <small class="helper-text">
        Define la distancia del coseno requerida para aceptar un caso empírico previo antes de consultar los manuales.
      </small>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const emit = defineEmits(['update-settings']);

const settings = reactive({
  userProfile: 'operator',
  similarityThreshold: 0.85
});

const emitUpdate = () => {
  emit('update-settings', {
    userProfile: settings.userProfile,
    similarityThreshold: settings.similarityThreshold
  });
};

// Emitir configuración inicial al montar el componente
emitUpdate();
</script>

<style scoped>
.equalizer-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  padding: 20px;
  margin-bottom: 20px;
  border-left: 4px solid #8e44ad;
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

.control-group {
  margin-bottom: 15px;
}

label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #34495e;
  font-size: 0.95rem;
}

select {
  width: 100%;
  padding: 8px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 0.95rem;
  background-color: #f8f9fa;
}

input[type="range"] {
  width: 100%;
  margin-top: 5px;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #95a5a6;
  margin-top: 5px;
}

.helper-text {
  display: block;
  font-size: 0.75rem;
  color: #7f8c8d;
  margin-top: 4px;
}
</style>