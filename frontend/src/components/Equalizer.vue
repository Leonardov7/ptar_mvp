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
        <button class="help-btn" @click.stop="(e) => togglePopover('profile', e)">?</button>
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
        <button class="help-btn" @click.stop="(e) => togglePopover('precision', e)">?</button>
      </label>
      <input 
        type="range" 
        id="threshold-slider" 
        min="0.2" 
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

    <!-- PORTAL DE BURBUJAS DE AYUDA AL BODY -->
    <Teleport to="body">
      <div v-if="activePopover === 'profile'" class="popover-content" :style="popoverStyle" @click.stop>
        <div class="popover-arrow"></div>
        <h4>Comportamiento del Asistente</h4>
        <p>El perfil ajusta la forma en que el sistema analiza la información y se comunica con usted:</p>
        <ul>
          <li><strong>Supervisor Operativo:</strong> Se enfoca en la práctica. Le dará instrucciones directas y fáciles de aplicar en campo para resolver el problema sin rodeos teóricos.</li>
          <li><strong>Ingeniero Ambiental:</strong> Se enfoca en el análisis profundo. Utilizará parámetros de calidad del agua y explicaciones científicas para diagnosticar la raíz de la falla.</li>
        </ul>
      </div>

      <div v-if="activePopover === 'precision'" class="popover-content" :style="popoverStyle" @click.stop>
        <div class="popover-arrow"></div>
        <h4>Aproximación de Casos</h4>
        <p>Esta barra controla qué tan exacto debe ser el problema que usted describe comparado con los reportes anteriores almacenados en la bitácora.</p>
        <ul>
          <li><strong>Hacia la derecha (Más Estricto):</strong> El sistema priorizará la lectura de documentación oficial, a menos que logre encontrar un caso empírico que sea idéntico a su problema.</li>
          <li><strong>Hacia la izquierda (Más Tolerante):</strong> El sistema le dará mayor peso a la experiencia de otros operarios, enlazando casos basándose en el contexto, incluso si utilizaron palabras distintas a las suyas.</li>
        </ul>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onBeforeUnmount } from 'vue';

const emit = defineEmits(['update-settings']);

const settings = reactive({
  userProfile: 'operator',
  similarityThreshold: 0.50
});

const activePopover = ref(null);
const popoverStyle = reactive({ top: '0px', left: '0px' });

const emitUpdate = () => {
  emit('update-settings', {
    userProfile: settings.userProfile,
    similarityThreshold: settings.similarityThreshold
  });
};

const togglePopover = (popoverName, event) => {
  if (activePopover.value === popoverName) {
    activePopover.value = null;
  } else {
    // Calculamos las coordenadas del botón interactuado de manera absoluta en el documento
    const rect = event.target.getBoundingClientRect();
    popoverStyle.top = `${rect.bottom + 12}px`;
    popoverStyle.left = `${rect.left - 15}px`;
    activePopover.value = popoverName;
  }
};

const closePopovers = () => {
  activePopover.value = null;
};

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

.help-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 20px;
  height: 20px;
  background-color: #3498db;
  color: white;
  border-radius: 50%;
  border: none;
  font-size: 0.85rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.help-btn:hover {
  background-color: #2980b9;
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

<style>
/* Estilos globales para el portal Teleport */
.popover-content {
  position: fixed;
  width: 320px;
  background-color: #ffffff;
  border: 1px solid #bdc3c7;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  z-index: 9999;
  cursor: default;
}

.popover-arrow {
  position: absolute;
  top: -6px;
  left: 20px;
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
}

.popover-content ul {
  margin: 0;
  padding-left: 20px;
  color: #34495e;
  font-size: 0.85rem;
}

.popover-content li {
  margin-bottom: 5px;
}
</style>