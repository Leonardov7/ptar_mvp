<template>
  <div class="equalizer-container">
    <div class="component-header">
      <h3>Ajustes de Inferencia</h3>
      <p>Configuración del comportamiento del sistema.</p>
    </div>

    <!-- CONTROL: PERFIL DEL ASISTENTE -->
    <div class="control-group">
      <label class="label-with-help">
        Perfil del Asistente:
        <div class="popover-wrapper">
          <button class="help-btn" @click.stop="togglePopover('profile')">?</button>
          
          <div class="popover-content" v-if="activePopover === 'profile'" @click.stop>
            <h4>¿Cómo afecta el Perfil al Modelo?</h4>
            <p><strong>1. Temperatura Generativa (Entropía):</strong> El Ingeniero opera con una temperatura de 0.0, lo que significa que el motor buscará siempre el token más probable matemáticamente, eliminando la creatividad para priorizar la exactitud algorítmica. El Operario opera a 0.1, permitiendo una ligera flexibilidad lingüística para que la respuesta suene más humana.</p>
            <p><strong>2. Inyección de Prompt del Sistema:</strong> Al cambiar el perfil, se altera el marco de referencia bajo el cual el modelo interpreta los vectores extraídos. El Ingeniero recibe la orden explícita de responder con termodinámica, cinética de reactores y parámetros fisicoquímicos. El Operario recibe la orden de traducir los hallazgos en instrucciones secuenciales de campo.</p>
          </div>
        </div>
      </label>
      <select id="profile-select" v-model="settings.userProfile" @change="emitUpdate">
        <option value="operator">Supervisor Operativo (Lenguaje directo)</option>
        <option value="engineer">Ingeniero Ambiental (Rigor científico)</option>
      </select>
    </div>

    <!-- CONTROL: PRECISIÓN DE BÚSQUEDA -->
    <div class="control-group">
      <label class="label-with-help">
        Precisión de Búsqueda Histórica ({{ settings.similarityThreshold }}):
        <div class="popover-wrapper">
          <button class="help-btn" @click.stop="togglePopover('precision')">?</button>
          
          <div class="popover-content" v-if="activePopover === 'precision'" @click.stop>
            <h4>Similitud del Coseno en el Espacio Vectorial</h4>
            <p>El sistema transforma el texto de su pregunta en un vector denso de 384 dimensiones. Esta barra controla la <strong>distancia matemática máxima</strong> permitida entre su vector de búsqueda y los vectores almacenados en la base de datos PostgreSQL.</p>
            <ul>
              <li><strong>Hacia 0.99 (Más Estricto):</strong> Exige que los síntomas descritos sean semánticamente idénticos al registro previo. Útil para evitar falsos positivos cuando el problema es muy específico.</li>
              <li><strong>Hacia 0.50 (Más Tolerante):</strong> Permite recuperar casos que tratan temas correlacionados, aunque las palabras utilizadas por el operario anterior hayan sido distintas. Si el umbral es muy bajo, el modelo puede intentar resolver un problema usando un contexto incorrecto.</li>
            </ul>
          </div>
        </div>
      </label>
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
        <span>Más tolerante</span>
        <span>Más estricto</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onBeforeUnmount } from 'vue';

const emit = defineEmits(['update-settings']);

const settings = reactive({
  userProfile: 'operator',
  similarityThreshold: 0.85
});

const activePopover = ref(null);

const emitUpdate = () => {
  emit('update-settings', {
    userProfile: settings.userProfile,
    similarityThreshold: settings.similarityThreshold
  });
};

const togglePopover = (popoverName) => {
  if (activePopover.value === popoverName) {
    activePopover.value = null;
  } else {
    activePopover.value = popoverName;
  }
};

const closePopovers = () => {
  activePopover.value = null;
};

// Escucha clics en cualquier parte de la ventana para cerrar los modales flotantes
onMounted(() => {
  document.addEventListener('click', closePopovers);
  emitUpdate();
});

onBeforeUnmount(() => {
  document.removeEventListener('click', closePopovers);
});
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
  margin-bottom: 25px;
}

.label-with-help {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #34495e;
  font-size: 0.95rem;
}

/* Lógica de Modales Flotantes */
.popover-wrapper {
  position: relative;
  display: inline-block;
}

.help-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 18px;
  height: 18px;
  background-color: #3498db;
  color: white;
  border-radius: 50%;
  border: none;
  font-size: 0.75rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.help-btn:hover {
  background-color: #2980b9;
}

.popover-content {
  position: absolute;
  top: 25px;
  left: 0;
  width: 320px;
  background-color: #ffffff;
  border: 1px solid #bdc3c7;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  z-index: 1000;
  cursor: default;
}

.popover-content::before {
  content: "";
  position: absolute;
  top: -6px;
  left: 5px;
  width: 10px;
  height: 10px;
  background-color: #ffffff;
  border-top: 1px solid #bdc3c7;
  border-left: 1px solid #bdc3c7;
  transform: rotate(45deg);
}

.popover-content h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 0.95rem;
  border-bottom: 1px solid #ecf0f1;
  padding-bottom: 5px;
}

.popover-content p {
  margin: 0 0 10px 0;
  color: #34495e;
  font-size: 0.85rem;
  line-height: 1.4;
  font-weight: normal;
}

.popover-content ul {
  margin: 0;
  padding-left: 20px;
  color: #34495e;
  font-size: 0.85rem;
  font-weight: normal;
}

.popover-content li {
  margin-bottom: 5px;
}

select {
  width: 100%;
  padding: 8px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 0.95rem;
  background-color: #f8f9fa;
  cursor: pointer;
}

input[type="range"] {
  width: 100%;
  margin-top: 5px;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #95a5a6;
  margin-top: 5px;
}
</style>